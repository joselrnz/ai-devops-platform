# MCP AWS Server

AI-powered AWS control server that exposes infrastructure operations as safe tools for LLMs via the Model Context Protocol (MCP).

## Overview

This project implements an enterprise-grade control plane that allows AI agents to interact with AWS infrastructure through a standardized protocol. It bridges the gap between natural language AI interfaces and cloud infrastructure management while maintaining security, auditability, and compliance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR IP ONLY                            │
│                    (Security Group Ingress)                     │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (REST)                         │
│                   + WAF (rate limiting)                         │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         VPC (10.0.0.0/16)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Public Subnet (10.0.1.0/24)                │    │
│  │         ┌─────────────────────────────────┐             │    │
│  │         │  ECS (EC2 t2.micro - free tier) │             │    │
│  │         │  - MCP Server Container         │             │    │
│  │         │  - FastAPI Container            │             │    │
│  │         └───────────────┬─────────────────┘             │    │
│  └─────────────────────────┼───────────────────────────────┘    │
│  ┌─────────────────────────┼───────────────────────────────┐    │
│  │              Private Subnet (10.0.2.0/24)               │    │
│  │         ┌───────────────▼─────────────────┐             │    │
│  │         │  RDS PostgreSQL (db.t3.micro)   │             │    │
│  │         │  - Audit logs                   │             │    │
│  │         │  - Tool configurations          │             │    │
│  │         └─────────────────────────────────┘             │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **MCP Protocol Implementation**: Expose AWS operations as standardized MCP tools
- **JSON-RPC Brokering**: Request handling with retry and circuit breaker patterns
- **IAM Integration**: Least-privilege role assumption per operation
- **Audit Logging**: Full audit trail to CloudWatch and RDS
- **Security First**: IP-restricted access, API keys, rate limiting

## MCP Tools Available

| Tool | Description | Operations |
|------|-------------|------------|
| `ec2` | EC2 instance management | list, describe, start, stop |
| `ecs` | ECS service management | list-services, describe-tasks, scale |
| `rds` | RDS database management | status, create-snapshot, list-snapshots |
| `cloudwatch` | CloudWatch monitoring | get-metrics, list-alarms, put-alarm |

## Tech Stack

- **Languages**: Python 3.11+, TypeScript
- **Framework**: FastAPI
- **Protocol**: MCP (Model Context Protocol), JSON-RPC 2.0
- **Infrastructure**: Terraform
- **AWS Services**: VPC, API Gateway, ECS, RDS, CloudWatch, IAM

## Project Structure

```
mcp-aws-server/
├── src/
│   ├── mcp_server/          # MCP server implementation
│   │   ├── server.py        # Main MCP server
│   │   ├── tools/           # AWS operation tools
│   │   └── handlers/        # JSON-RPC handlers
│   ├── api/                 # FastAPI REST layer
│   └── utils/               # Shared utilities
├── infra/                   # Terraform infrastructure
│   ├── modules/             # Reusable modules
│   └── environments/        # Environment configs
├── tests/                   # Unit and integration tests
└── docs/                    # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- Terraform 1.5+
- AWS CLI configured
- Docker (optional, for local development)

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-aws-server.git
cd mcp-aws-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run the MCP server locally
python -m src.mcp_server.server
```

### Deploy Infrastructure

```bash
# Navigate to dev environment
cd infra/environments/dev

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Deploy (set your IP in terraform.tfvars first!)
terraform apply

# Destroy when done (to avoid charges)
terraform destroy
```

## Configuration

Create `infra/environments/dev/terraform.tfvars`:

```hcl
# Your public IP for security group access
allowed_ip = "YOUR_PUBLIC_IP/32"

# AWS region
aws_region = "us-east-1"

# Project naming
project_name = "mcp-server"
environment  = "dev"
```

## Security

- **Network**: All ingress restricted to your IP address
- **Authentication**: API Gateway API keys required
- **Authorization**: IAM roles with least-privilege policies
- **Audit**: All operations logged to CloudWatch and RDS
- **Encryption**: TLS in transit, encryption at rest for RDS

## Cost Estimate

| Resource | Monthly Cost |
|----------|--------------|
| EC2 t2.micro | $0 (free tier) |
| RDS db.t3.micro | $0 (free tier) |
| API Gateway | $0 (< 1M calls) |
| CloudWatch | ~$0-2 |
| S3 (TF state) | ~$0.02 |
| **Total** | **~$0-5/month** |

## Documentation

- [Architecture Deep Dive](docs/architecture.md)
- [MCP Tools Reference](docs/mcp-tools.md)
- [Security Model](docs/security.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Jose** | DevOps & Cloud Engineer
