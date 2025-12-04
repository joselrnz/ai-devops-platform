"""
MCP Server - Main entry point for the Model Context Protocol server.

This server exposes AWS operations as MCP tools that can be called by AI agents.
Implements JSON-RPC 2.0 protocol over stdio and HTTP.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Import tools
from .tools.ec2_tools import EC2Tools
from .tools.ecs_tools import ECSTools
from .tools.rds_tools import RDSTools
from .tools.cloudwatch_tools import CloudWatchTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """JSON-RPC 2.0 request format"""

    jsonrpc: str = Field(default="2.0")
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class MCPResponse(BaseModel):
    """JSON-RPC 2.0 response format"""

    jsonrpc: str = Field(default="2.0")
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class MCPServer:
    """
    MCP Server implementing the Model Context Protocol.

    Provides AWS operations as tools accessible via JSON-RPC 2.0.
    """

    def __init__(self):
        """Initialize MCP server with AWS tools"""
        self.tools: Dict[str, Any] = {}
        self._initialize_tools()

    def _initialize_tools(self) -> None:
        """Initialize all AWS operation tools"""
        logger.info("Initializing MCP tools...")

        # EC2 Tools
        self.tools["ec2"] = EC2Tools()

        # ECS Tools
        self.tools["ecs"] = ECSTools()

        # RDS Tools
        self.tools["rds"] = RDSTools()

        # CloudWatch Tools
        self.tools["cloudwatch"] = CloudWatchTools()

        logger.info(f"Initialized {len(self.tools)} tool categories")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Return list of available MCP tools.

        Returns:
            List of tool definitions with names, descriptions, and schemas
        """
        tools_list = []

        for category, tool_instance in self.tools.items():
            tools_list.extend(tool_instance.get_tools())

        return tools_list

    async def call_tool(
        self, tool_name: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool by name with given parameters.

        Args:
            tool_name: Name of the tool (e.g., "ec2.list_instances")
            parameters: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or execution fails
        """
        # Parse tool name (category.operation)
        if "." not in tool_name:
            raise ValueError(f"Invalid tool name format: {tool_name}")

        category, operation = tool_name.split(".", 1)

        if category not in self.tools:
            raise ValueError(f"Unknown tool category: {category}")

        tool_instance = self.tools[category]

        # Execute tool
        logger.info(f"Executing tool: {tool_name} with params: {parameters}")
        result = await tool_instance.execute(operation, parameters or {})

        logger.info(f"Tool {tool_name} executed successfully")
        return result

    async def handle_request(self, request_data: Dict[str, Any]) -> MCPResponse:
        """
        Handle incoming JSON-RPC 2.0 request.

        Args:
            request_data: JSON-RPC request

        Returns:
            JSON-RPC response
        """
        try:
            request = MCPRequest(**request_data)

            # Handle different RPC methods
            if request.method == "tools/list":
                # List available tools
                tools = self.list_tools()
                return MCPResponse(
                    result={"tools": tools},
                    id=request.id,
                )

            elif request.method == "tools/call":
                # Call a specific tool
                if not request.params:
                    raise ValueError("Missing parameters for tools/call")

                tool_name = request.params.get("name")
                tool_params = request.params.get("arguments", {})

                if not tool_name:
                    raise ValueError("Missing 'name' in parameters")

                result = await self.call_tool(tool_name, tool_params)

                return MCPResponse(
                    result=result,
                    id=request.id,
                )

            elif request.method == "initialize":
                # Initialize connection
                return MCPResponse(
                    result={
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                        },
                        "serverInfo": {
                            "name": "mcp-aws-server",
                            "version": "0.1.0",
                        },
                    },
                    id=request.id,
                )

            else:
                raise ValueError(f"Unknown method: {request.method}")

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            return MCPResponse(
                error={
                    "code": -32603,
                    "message": str(e),
                },
                id=request_data.get("id"),
            )

    async def run_stdio(self) -> None:
        """
        Run MCP server over stdio (standard input/output).

        Used for direct integration with MCP clients like Claude Desktop.
        """
        logger.info("Starting MCP server on stdio...")

        while True:
            try:
                # Read JSON-RPC request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )

                if not line:
                    break

                request_data = json.loads(line.strip())

                # Handle request
                response = await self.handle_request(request_data)

                # Write JSON-RPC response to stdout
                print(response.model_dump_json(), flush=True)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.error(f"Error in stdio loop: {e}", exc_info=True)


def main() -> None:
    """Main entry point for MCP server"""
    logger.info("Starting MCP AWS Server...")

    server = MCPServer()

    # Run server on stdio
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
