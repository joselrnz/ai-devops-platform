package v1alpha1

import (
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// AgentDeploymentSpec defines the desired state of AgentDeployment
type AgentDeploymentSpec struct {
	// Model is the LLM model to deploy
	// +kubebuilder:validation:Required
	// +kubebuilder:validation:Enum=claude-3-opus;claude-3-sonnet;claude-3-haiku;gpt-4;gpt-4-turbo;gpt-3.5-turbo;llama-2-70b;mixtral-8x7b
	Model string `json:"model"`

	// Replicas is the number of desired pods
	// +optional
	// +kubebuilder:default=2
	// +kubebuilder:validation:Minimum=0
	// +kubebuilder:validation:Maximum=100
	Replicas *int32 `json:"replicas,omitempty"`

	// Autoscaling configuration
	// +optional
	Autoscaling *AutoscalingSpec `json:"autoscaling,omitempty"`

	// Resources defines the resource requirements
	// +optional
	Resources corev1.ResourceRequirements `json:"resources,omitempty"`

	// SecurityContext defines security settings
	// +optional
	SecurityContext *SecurityContextSpec `json:"securityContext,omitempty"`

	// Secrets to inject as environment variables
	// +optional
	Secrets []SecretReference `json:"secrets,omitempty"`

	// Monitoring configuration
	// +optional
	Monitoring *MonitoringSpec `json:"monitoring,omitempty"`

	// Ingress configuration
	// +optional
	Ingress *IngressSpec `json:"ingress,omitempty"`
}

// AutoscalingSpec defines autoscaling configuration
type AutoscalingSpec struct {
	// Enabled determines if autoscaling is enabled
	// +optional
	// +kubebuilder:default=true
	Enabled bool `json:"enabled,omitempty"`

	// MinReplicas is the minimum number of replicas
	// +optional
	// +kubebuilder:default=2
	// +kubebuilder:validation:Minimum=1
	MinReplicas *int32 `json:"minReplicas,omitempty"`

	// MaxReplicas is the maximum number of replicas
	// +optional
	// +kubebuilder:default=10
	// +kubebuilder:validation:Minimum=1
	// +kubebuilder:validation:Maximum=100
	MaxReplicas *int32 `json:"maxReplicas,omitempty"`

	// Metrics contains the specifications for which to use to calculate the desired replica count
	// +optional
	Metrics []interface{} `json:"metrics,omitempty"`
}

// SecurityContextSpec defines security context
type SecurityContextSpec struct {
	// RunAsNonRoot ensures the container runs as a non-root user
	// +optional
	// +kubebuilder:default=true
	RunAsNonRoot *bool `json:"runAsNonRoot,omitempty"`

	// ReadOnlyRootFilesystem mounts the container's root filesystem as read-only
	// +optional
	// +kubebuilder:default=true
	ReadOnlyRootFilesystem *bool `json:"readOnlyRootFilesystem,omitempty"`

	// RunAsUser is the UID to run the entrypoint of the container process
	// +optional
	// +kubebuilder:default=1000
	RunAsUser *int64 `json:"runAsUser,omitempty"`
}

// SecretReference references a secret and key
type SecretReference struct {
	// Name of the secret
	// +kubebuilder:validation:Required
	Name string `json:"name"`

	// Key in the secret
	// +kubebuilder:validation:Required
	Key string `json:"key"`
}

// MonitoringSpec defines monitoring configuration
type MonitoringSpec struct {
	// Enabled determines if monitoring is enabled
	// +optional
	// +kubebuilder:default=true
	Enabled bool `json:"enabled,omitempty"`

	// ScrapeInterval is the Prometheus scrape interval
	// +optional
	// +kubebuilder:default="30s"
	ScrapeInterval string `json:"scrapeInterval,omitempty"`
}

// IngressSpec defines ingress configuration
type IngressSpec struct {
	// Enabled determines if ingress is enabled
	// +optional
	// +kubebuilder:default=false
	Enabled bool `json:"enabled,omitempty"`

	// Host is the hostname for the ingress
	// +optional
	Host string `json:"host,omitempty"`

	// TLS enables TLS for the ingress
	// +optional
	// +kubebuilder:default=true
	TLS bool `json:"tls,omitempty"`
}

// AgentDeploymentStatus defines the observed state of AgentDeployment
type AgentDeploymentStatus struct {
	// Conditions represent the latest available observations of an object's state
	// +optional
	Conditions []metav1.Condition `json:"conditions,omitempty"`

	// Replicas is the most recently observed number of replicas
	// +optional
	Replicas int32 `json:"replicas,omitempty"`

	// ReadyReplicas is the number of pods with a Ready condition
	// +optional
	ReadyReplicas int32 `json:"readyReplicas,omitempty"`

	// AvailableReplicas is the number of available replicas
	// +optional
	AvailableReplicas int32 `json:"availableReplicas,omitempty"`

	// Phase represents the current phase of the agent deployment
	// +optional
	// +kubebuilder:validation:Enum=Pending;Running;Failed;Scaling
	Phase string `json:"phase,omitempty"`

	// ObservedGeneration reflects the generation of the most recently observed AgentDeployment
	// +optional
	ObservedGeneration int64 `json:"observedGeneration,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:subresource:scale:specpath=.spec.replicas,statuspath=.status.replicas
// +kubebuilder:printcolumn:name="Model",type=string,JSONPath=`.spec.model`
// +kubebuilder:printcolumn:name="Replicas",type=integer,JSONPath=`.status.replicas`
// +kubebuilder:printcolumn:name="Ready",type=integer,JSONPath=`.status.readyReplicas`
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`

// AgentDeployment is the Schema for the agentdeployments API
type AgentDeployment struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   AgentDeploymentSpec   `json:"spec,omitempty"`
	Status AgentDeploymentStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true

// AgentDeploymentList contains a list of AgentDeployment
type AgentDeploymentList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []AgentDeployment `json:"items"`
}

func init() {
	SchemeBuilder.Register(&AgentDeployment{}, &AgentDeploymentList{})
}
