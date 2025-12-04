# Security Model

## Defense in Depth

### 1. Network Layer
- VPC isolation with security groups
- IP-restricted access (your IP only)
- No NAT Gateway (cost optimization + security groups)

### 2. Authentication & Authorization
- API Gateway API keys
- IAM roles with least-privilege policies
- Tag-based conditional access

### 3. Audit & Compliance
- All operations logged to CloudWatch and RDS
- 90-day retention for compliance
- Immutable audit trail

### 4. Application Security
- Circuit breaker pattern (prevents cascading failures)
- Rate limiting per tool
- Input validation on all requests

## IAM Policy Example

```json
{
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ec2:StartInstances", "ec2:StopInstances"],
    "Resource": "*",
    "Condition": {
      "StringEquals": {
        "ec2:ResourceTag/ManagedBy": "mcp-server"
      }
    }
  }]
}
```

## Audit Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-123",
  "user": "ai-agent-001",
  "tool": "ec2",
  "operation": "stop_instance",
  "arguments": {"instance_id": "i-abc123"},
  "result": "success",
  "duration_ms": 245
}
```

## Security Best Practices

1. **Rotate API keys** every 90 days
2. **Monitor audit logs** for suspicious activity
3. **Use least-privilege IAM roles** for all operations
4. **Enable CloudWatch alarms** for security events
5. **Review security groups** monthly
6. **Keep dependencies updated** (Dependabot enabled)

## Compliance

- AWS Well-Architected Framework
- CIS AWS Foundations Benchmark
- GDPR-ready (data protection controls)
