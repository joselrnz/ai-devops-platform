# MCP Tools Reference

Complete reference for all AWS tools exposed via MCP.

## EC2 Tool

### Operations
- `list` - List EC2 instances with filters
- `describe` - Get instance details
- `start` - Start stopped instance
- `stop` - Stop running instance

**Example:**
```json
{
  "operation": "list",
  "filters": [{"Name": "instance-state-name", "Values": ["running"]}],
  "max_results": 50
}
```

## ECS Tool

### Operations
- `list-clusters` - List all ECS clusters
- `list-services` - List services in cluster
- `describe-service` - Get service details
- `scale` - Scale service to desired count
- `list-tasks` - List tasks in cluster/service
- `describe-tasks` - Get task details

## RDS Tool

### Operations
- `list-instances` - List all RDS instances
- `describe-instance` - Get instance details
- `status` - Get current status
- `create-snapshot` - Create manual snapshot
- `list-snapshots` - List available snapshots

## CloudWatch Tool

### Operations
- `get-metrics` - Get metric statistics
- `list-alarms` - List CloudWatch alarms
- `put-alarm` - Create or update alarm

## Rate Limits

- EC2: 100 requests/minute
- ECS: 100 requests/minute
- RDS: 50 requests/minute
- CloudWatch: 150 requests/minute
