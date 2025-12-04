import React, { useState } from 'react';

const projects = [
  {
    id: 1,
    name: "LLM Control Plane",
    shortName: "AWS Ops",
    category: "AI Infrastructure",
    layer: 3,
    color: "#3182ce",
    description: "AI-native control plane exposing AWS operations as MCP tools",
    tech: ["Python", "MCP", "FastAPI", "Lambda", "IAM", "EventBridge"],
    capabilities: [
      "Expose AWS ops as MCP tools",
      "JSON-RPC request brokering",
      "IAM role assumption",
      "Audit logging"
    ]
  },
  {
    id: 2,
    name: "LLM Security Gateway",
    shortName: "Security",
    category: "AI Security",
    layer: 2,
    color: "#e53e3e",
    description: "Enterprise gateway enforcing DLP, PII redaction, RBAC",
    tech: ["Python", "FastAPI", "Redis", "OPA/Rego", "Presidio"],
    capabilities: [
      "DLP scanning",
      "PII redaction",
      "RBAC enforcement",
      "Model routing"
    ]
  },
  {
    id: 3,
    name: "K8s AgentOps Platform",
    shortName: "K8s Agents",
    category: "Kubernetes",
    layer: 3,
    color: "#38a169",
    description: "AI agents as K8s workloads with scoped MCP permissions",
    tech: ["Kubernetes", "Helm", "ArgoCD", "OPA Gatekeeper", "Falco"],
    capabilities: [
      "Agent workload orchestration",
      "Namespace-scoped RBAC",
      "NetworkPolicy isolation",
      "GitOps deployment"
    ]
  },
  {
    id: 4,
    name: "CI/CD Framework",
    shortName: "CI/CD",
    category: "DevOps",
    layer: 3,
    color: "#805ad5",
    description: "Standardized pipelines with security scanning and GitOps",
    tech: ["GitHub Actions", "ArgoCD", "Trivy", "SonarQube", "Syft"],
    capabilities: [
      "Multi-stage pipelines",
      "SAST/DAST scanning",
      "SBOM generation",
      "Canary deployments"
    ]
  },
  {
    id: 5,
    name: "Logging & Threat Analytics",
    shortName: "Logging",
    category: "Security",
    layer: 4,
    color: "#dd6b20",
    description: "Centralized log aggregation with security correlation",
    tech: ["OpenSearch", "Fluent Bit", "Splunk", "DataDog", "OTEL"],
    capabilities: [
      "Log aggregation",
      "Threat correlation",
      "Anomaly detection",
      "Compliance reporting"
    ]
  },
  {
    id: 6,
    name: "Observability Fabric",
    shortName: "Observability",
    category: "Monitoring",
    layer: 4,
    color: "#d69e2e",
    description: "Unified metrics, logs, traces across multi-cloud",
    tech: ["Prometheus", "Grafana", "Loki", "Tempo", "OTEL"],
    capabilities: [
      "OTEL collection",
      "Distributed tracing",
      "SLO management",
      "Multi-cloud federation"
    ]
  },
  {
    id: 7,
    name: "NL Automation Hub",
    shortName: "Voice/Chat",
    category: "Automation",
    layer: 1,
    color: "#319795",
    description: "Voice/chat interface for natural language infrastructure control",
    tech: ["n8n", "Node.js", "Claude/GPT", "Whisper", "Twilio"],
    capabilities: [
      "NL intent recognition",
      "Voice input support",
      "Workflow orchestration",
      "Human-in-the-loop"
    ]
  }
];

const layers = [
  { id: 1, name: "User Interface", color: "#ebf8ff" },
  { id: 2, name: "Security & Governance", color: "#fed7d7" },
  { id: 3, name: "Control Planes", color: "#e9d8fd" },
  { id: 4, name: "Observability", color: "#feebc8" }
];

export default function ArchitectureDiagram() {
  const [selected, setSelected] = useState(null);
  const [hoveredLayer, setHoveredLayer] = useState(null);

  const selectedProject = projects.find(p => p.id === selected);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">AI-Augmented DevOps Platform</h1>
        <p className="text-gray-600 mb-6">Click any component to see details</p>
        
        <div className="flex gap-6">
          {/* Architecture Diagram */}
          <div className="flex-1">
            <div className="bg-white rounded-xl shadow-lg p-4 space-y-3">
              {layers.map(layer => (
                <div 
                  key={layer.id}
                  className="rounded-lg p-3 transition-all duration-200"
                  style={{ 
                    backgroundColor: hoveredLayer === layer.id ? layer.color : `${layer.color}88`
                  }}
                  onMouseEnter={() => setHoveredLayer(layer.id)}
                  onMouseLeave={() => setHoveredLayer(null)}
                >
                  <div className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                    Layer {layer.id}: {layer.name}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {projects.filter(p => p.layer === layer.id).map(project => (
                      <button
                        key={project.id}
                        onClick={() => setSelected(selected === project.id ? null : project.id)}
                        className={`
                          px-4 py-3 rounded-lg font-medium text-white text-sm
                          transition-all duration-200 transform
                          ${selected === project.id ? 'ring-4 ring-offset-2 scale-105' : 'hover:scale-102'}
                        `}
                        style={{ 
                          backgroundColor: project.color,
                          ringColor: project.color
                        }}
                      >
                        <div className="font-bold">[{project.id}]</div>
                        <div>{project.shortName}</div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Data Flow Arrows */}
            <div className="mt-4 bg-white rounded-xl shadow-lg p-4">
              <h3 className="font-semibold text-gray-700 mb-3">Data Flow</h3>
              <div className="text-sm text-gray-600 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg">↓</span>
                  <span>[7] Voice/Chat → [2] Security Gateway → [1,3,4] Control Planes</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg">↓</span>
                  <span>[1,3,4] Control Planes → [5,6] Observability Fabric</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg">↑</span>
                  <span>[5,6] Alerts → [7] Automated Response</span>
                </div>
              </div>
            </div>
          </div>

          {/* Detail Panel */}
          <div className="w-80">
            {selectedProject ? (
              <div 
                className="bg-white rounded-xl shadow-lg p-5 sticky top-6"
                style={{ borderTop: `4px solid ${selectedProject.color}` }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <span 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                    style={{ backgroundColor: selectedProject.color }}
                  >
                    {selectedProject.id}
                  </span>
                  <div>
                    <h2 className="font-bold text-gray-800">{selectedProject.name}</h2>
                    <span className="text-xs text-gray-500">{selectedProject.category}</span>
                  </div>
                </div>
                
                <p className="text-sm text-gray-600 mb-4">{selectedProject.description}</p>
                
                <div className="mb-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Capabilities</h3>
                  <ul className="space-y-1">
                    {selectedProject.capabilities.map((cap, i) => (
                      <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                        <span className="text-green-500 mt-0.5">✓</span>
                        {cap}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Tech Stack</h3>
                  <div className="flex flex-wrap gap-1">
                    {selectedProject.tech.map((t, i) => (
                      <span 
                        key={i}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-lg p-5 text-center text-gray-500">
                <div className="text-4xl mb-2">👆</div>
                <p>Select a component to view details</p>
              </div>
            )}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="mt-6 grid grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">7</div>
            <div className="text-sm text-gray-600">Projects</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-green-600">4</div>
            <div className="text-sm text-gray-600">Layers</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">18</div>
            <div className="text-sm text-gray-600">Weeks to MVP</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">MCP</div>
            <div className="text-sm text-gray-600">AI Protocol</div>
          </div>
        </div>
      </div>
    </div>
  );
}