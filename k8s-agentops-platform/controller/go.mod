module github.com/yourusername/k8s-agentops-platform/controller

go 1.21

require (
	k8s.io/api v0.28.4
	k8s.io/apimachinery v0.28.4
	k8s.io/client-go v0.28.4
	sigs.k8s.io/controller-runtime v0.16.3
)

require (
	github.com/go-logr/logr v1.3.0
	github.com/prometheus/client_golang v1.17.0
	go.uber.org/zap v1.26.0
)
