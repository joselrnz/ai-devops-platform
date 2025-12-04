package controllers

import (
	"context"
	"fmt"
	"time"

	"github.com/go-logr/logr"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

	agentopsv1alpha1 "github.com/yourusername/k8s-agentops-platform/controller/pkg/apis/agentops/v1alpha1"
)

const (
	agentDeploymentFinalizer = "agentops.io/finalizer"
	defaultImage             = "ghcr.io/myorg/llm-agent"
)

// AgentDeploymentReconciler reconciles an AgentDeployment object
type AgentDeploymentReconciler struct {
	client.Client
	Scheme *runtime.Scheme
	Log    logr.Logger
}

// +kubebuilder:rbac:groups=agentops.io,resources=agentdeployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=agentops.io,resources=agentdeployments/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=agentops.io,resources=agentdeployments/finalizers,verbs=update
// +kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=core,resources=services,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=autoscaling,resources=horizontalpodautoscalers,verbs=get;list;watch;create;update;patch;delete

// Reconcile is part of the main kubernetes reconciliation loop
func (r *AgentDeploymentReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := r.Log.WithValues("agentdeployment", req.NamespacedName)

	// Fetch the AgentDeployment instance
	agentDep := &agentopsv1alpha1.AgentDeployment{}
	err := r.Get(ctx, req.NamespacedName, agentDep)
	if err != nil {
		if errors.IsNotFound(err) {
			log.Info("AgentDeployment resource not found. Ignoring since object must be deleted")
			return ctrl.Result{}, nil
		}
		log.Error(err, "Failed to get AgentDeployment")
		return ctrl.Result{}, err
	}

	// Handle deletion
	if !agentDep.ObjectMeta.DeletionTimestamp.IsZero() {
		if controllerutil.ContainsFinalizer(agentDep, agentDeploymentFinalizer) {
			// Run finalization logic
			if err := r.finalizeAgentDeployment(ctx, agentDep); err != nil {
				return ctrl.Result{}, err
			}

			// Remove finalizer
			controllerutil.RemoveFinalizer(agentDep, agentDeploymentFinalizer)
			if err := r.Update(ctx, agentDep); err != nil {
				return ctrl.Result{}, err
			}
		}
		return ctrl.Result{}, nil
	}

	// Add finalizer if not present
	if !controllerutil.ContainsFinalizer(agentDep, agentDeploymentFinalizer) {
		controllerutil.AddFinalizer(agentDep, agentDeploymentFinalizer)
		if err := r.Update(ctx, agentDep); err != nil {
			return ctrl.Result{}, err
		}
	}

	// Reconcile Deployment
	deployment := &appsv1.Deployment{}
	err = r.Get(ctx, types.NamespacedName{Name: agentDep.Name, Namespace: agentDep.Namespace}, deployment)
	if err != nil && errors.IsNotFound(err) {
		// Create new Deployment
		dep := r.deploymentForAgentDeployment(agentDep)
		log.Info("Creating a new Deployment", "Deployment.Namespace", dep.Namespace, "Deployment.Name", dep.Name)
		err = r.Create(ctx, dep)
		if err != nil {
			log.Error(err, "Failed to create new Deployment", "Deployment.Namespace", dep.Namespace, "Deployment.Name", dep.Name)
			return ctrl.Result{}, err
		}
		return ctrl.Result{Requeue: true}, nil
	} else if err != nil {
		log.Error(err, "Failed to get Deployment")
		return ctrl.Result{}, err
	}

	// Update the AgentDeployment status
	if err := r.updateStatus(ctx, agentDep, deployment); err != nil {
		return ctrl.Result{}, err
	}

	return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
}

// deploymentForAgentDeployment returns a Deployment object
func (r *AgentDeploymentReconciler) deploymentForAgentDeployment(ad *agentopsv1alpha1.AgentDeployment) *appsv1.Deployment {
	labels := labelsForAgentDeployment(ad.Name)
	replicas := ad.Spec.Replicas
	if replicas == nil {
		defaultReplicas := int32(2)
		replicas = &defaultReplicas
	}

	// Determine image based on model
	image := fmt.Sprintf("%s:%s", defaultImage, ad.Spec.Model)

	dep := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      ad.Name,
			Namespace: ad.Namespace,
			Labels:    labels,
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{
						Image: image,
						Name:  "agent",
						Ports: []corev1.ContainerPort{{
							ContainerPort: 8080,
							Name:          "http",
						}},
						Resources: ad.Spec.Resources,
						LivenessProbe: &corev1.Probe{
							ProbeHandler: corev1.ProbeHandler{
								HTTPGet: &corev1.HTTPGetAction{
									Path: "/health",
									Port: intstr.FromInt(8080),
								},
							},
							InitialDelaySeconds: 30,
							PeriodSeconds:       10,
						},
						ReadinessProbe: &corev1.Probe{
							ProbeHandler: corev1.ProbeHandler{
								HTTPGet: &corev1.HTTPGetAction{
									Path: "/ready",
									Port: intstr.FromInt(8080),
								},
							},
							InitialDelaySeconds: 10,
							PeriodSeconds:       5,
						},
					}},
				},
			},
		},
	}

	// Set AgentDeployment instance as the owner
	controllerutil.SetControllerReference(ad, dep, r.Scheme)
	return dep
}

// updateStatus updates the AgentDeployment status
func (r *AgentDeploymentReconciler) updateStatus(ctx context.Context, ad *agentopsv1alpha1.AgentDeployment, dep *appsv1.Deployment) error {
	ad.Status.Replicas = dep.Status.Replicas
	ad.Status.ReadyReplicas = dep.Status.ReadyReplicas
	ad.Status.AvailableReplicas = dep.Status.AvailableReplicas

	// Update phase
	if dep.Status.ReadyReplicas == *dep.Spec.Replicas {
		ad.Status.Phase = "Running"
	} else if dep.Status.ReadyReplicas > 0 {
		ad.Status.Phase = "Scaling"
	} else {
		ad.Status.Phase = "Pending"
	}

	ad.Status.ObservedGeneration = ad.Generation

	return r.Status().Update(ctx, ad)
}

// finalizeAgentDeployment handles cleanup before deletion
func (r *AgentDeploymentReconciler) finalizeAgentDeployment(ctx context.Context, ad *agentopsv1alpha1.AgentDeployment) error {
	r.Log.Info("Finalizing AgentDeployment", "Name", ad.Name, "Namespace", ad.Namespace)
	// Add cleanup logic here (e.g., delete external resources)
	return nil
}

// labelsForAgentDeployment returns the labels for selecting the resources
func labelsForAgentDeployment(name string) map[string]string {
	return map[string]string{
		"app.kubernetes.io/name":     "agent",
		"app.kubernetes.io/instance": name,
		"app.kubernetes.io/managed-by": "agentops-controller",
	}
}

// SetupWithManager sets up the controller with the Manager
func (r *AgentDeploymentReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&agentopsv1alpha1.AgentDeployment{}).
		Owns(&appsv1.Deployment{}).
		Complete(r)
}
