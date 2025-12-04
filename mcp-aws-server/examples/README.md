# MCP AWS Server Examples

This directory contains example code and configurations for using the MCP AWS Server.

## Examples

### 1. Python Client (`client_example.py`)

A complete Python client demonstrating how to interact with the MCP server programmatically.

**Usage:**
```bash
# Install dependencies
pip install httpx

# Run the example
python examples/client_example.py
```

**What it demonstrates:**
- Listing available tools
- Calling EC2 operations (list, describe)
- Filtering instances by state
- Managing ECS services (scale)
- Creating RDS snapshots
- Querying CloudWatch metrics

### 2. Claude Desktop Integration (`claude_desktop_config.json`)

Configuration file for integrating the MCP server with Claude Desktop app.

**Setup:**

1. Locate your Claude Desktop config directory:
   - **macOS**: `~/Library/Application Support/Claude/`
   - **Windows**: `%APPDATA%\Claude\`
   - **Linux**: `~/.config/Claude/`

2. Copy the example config:
   ```bash
   cp examples/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. Update the `cwd` path to your project directory

4. Restart Claude Desktop

5. Claude will now have access to AWS tools via MCP!

**Example Claude conversation:**
```
You: "List my running EC2 instances"

Claude: *calls ec2 tool with operation: list*
"You have 3 running EC2 instances:
1. web-server-1 (t2.micro) - 203.0.113.45
2. api-server-1 (t2.small) - 203.0.113.46
3. worker-1 (t2.micro) - 203.0.113.47"

You: "Stop the worker instance"

Claude: *calls ec2 tool with operation: stop*
"The worker-1 instance (i-abc123) is now stopping."
```

## Quick Start Scripts

### Start Local Server

```bash
#!/bin/bash
# start_server.sh

# Activate virtual environment
source venv/bin/activate

# Set AWS credentials
export AWS_REGION=us-east-1
export AWS_PROFILE=default

# Start the MCP server
python -m src.mcp_server.server
```

### Test Connection

```bash
#!/bin/bash
# test_connection.sh

curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/list",
    "params": {}
  }' | jq
```

## Advanced Examples

### Batch Operations

```python
async def batch_stop_instances(client, instance_ids):
    """Stop multiple instances in batch."""
    tasks = []
    for instance_id in instance_ids:
        task = client.call_tool(
            tool_name="ec2",
            arguments={
                "operation": "stop",
                "instance_id": instance_id
            }
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### Error Handling

```python
try:
    response = await client.call_tool(
        tool_name="ec2",
        arguments={"operation": "describe", "instance_id": "i-invalid"}
    )
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        print("Rate limit exceeded. Retrying in 30 seconds...")
        await asyncio.sleep(30)
    elif e.response.status_code == 500:
        print("Server error. Check circuit breaker status.")
    else:
        print(f"HTTP error: {e}")
```

### Monitoring with Audit Logs

```python
# Query audit logs from RDS
async def get_audit_logs(start_time, end_time):
    """Fetch audit logs for compliance reporting."""
    query = """
    SELECT
        timestamp,
        user,
        tool,
        operation,
        result
    FROM audit_logs
    WHERE timestamp BETWEEN %s AND %s
    ORDER BY timestamp DESC
    """

    async with asyncpg.connect(DATABASE_URL) as conn:
        rows = await conn.fetch(query, start_time, end_time)
        return rows
```

## Best Practices

1. **Authentication**: Always use API keys in production
2. **Error Handling**: Implement retry logic with exponential backoff
3. **Rate Limiting**: Respect the rate limits (see docs/mcp-tools.md)
4. **Audit Logs**: Monitor audit logs for suspicious activity
5. **Circuit Breaker**: Handle circuit breaker open states gracefully

## Troubleshooting

### Server Not Responding

```bash
# Check if server is running
ps aux | grep "mcp_server.server"

# Check logs
tail -f logs/mcp-server.log

# Test health endpoint
curl http://localhost:8000/health
```

### Authentication Errors

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM role permissions
aws iam get-role --role-name mcp-server-role
```

### Circuit Breaker Open

The circuit breaker opens when AWS services are experiencing issues. Wait 60 seconds for automatic recovery.

```json
{
  "error": {
    "code": -32000,
    "message": "Circuit breaker is OPEN",
    "data": {
      "retry_after": 60
    }
  }
}
```

## Additional Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [AWS SDK for Python (boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Project Documentation](../docs/)
