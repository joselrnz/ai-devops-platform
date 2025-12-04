"""
FastAPI REST Layer - HTTP interface for MCP server.

Provides REST endpoints for clients that don't speak MCP directly.
Wraps MCP protocol in HTTP for easier integration.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..mcp_server.server import MCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP AWS Server",
    description="REST API for AWS operations via Model Context Protocol",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP server
mcp_server = MCPServer()


# Request/Response models
class ToolCallRequest(BaseModel):
    """Request to call a tool"""
    tool_name: str = Field(..., description="Name of the tool (e.g., 'ec2.list_instances')")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Tool parameters")


class ToolCallResponse(BaseModel):
    """Response from tool call"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    tools_available: int


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    tools = mcp_server.list_tools()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        tools_available=len(tools),
    )


@app.get("/api/v1/tools")
async def list_tools():
    """
    List all available MCP tools.

    Returns:
        List of tool definitions with schemas
    """
    tools = mcp_server.list_tools()
    return {
        "tools": tools,
        "count": len(tools),
    }


@app.post("/api/v1/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """
    Call a specific tool with parameters.

    Args:
        request: Tool call request with name and parameters

    Returns:
        Tool execution result
    """
    try:
        logger.info(f"REST API: Calling tool {request.tool_name}")

        result = await mcp_server.call_tool(
            tool_name=request.tool_name,
            parameters=request.parameters,
        )

        return ToolCallResponse(
            success=True,
            result=result,
        )

    except ValueError as e:
        logger.error(f"Invalid tool call: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error executing tool: {e}", exc_info=True)
        return ToolCallResponse(
            success=False,
            error=str(e),
        )


@app.get("/api/v1/tools/{category}")
async def list_tools_by_category(category: str):
    """
    List tools by category.

    Args:
        category: Tool category (ec2, ecs, rds, cloudwatch)

    Returns:
        Filtered list of tools
    """
    all_tools = mcp_server.list_tools()

    # Filter tools by category
    category_tools = [
        tool for tool in all_tools
        if tool["name"].startswith(f"{category}.")
    ]

    if not category_tools:
        raise HTTPException(
            status_code=404,
            detail=f"No tools found for category: {category}"
        )

    return {
        "category": category,
        "tools": category_tools,
        "count": len(category_tools),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


def main():
    """Run FastAPI server"""
    import uvicorn

    logger.info("Starting FastAPI server...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
