"""
LangGraph Agent - State-based agent orchestration.

Implements the main agent workflow using LangGraph for:
- Intent parsing
- Tool selection and execution
- Multi-step reasoning
- Response synthesis
"""

import logging
from typing import TypedDict, List, Optional, Annotated, Literal
from datetime import datetime, UTC
import operator

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from ..tools.registry import tool_registry
from ..config.settings import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Agent State Definition
# ============================================================================

class AgentState(TypedDict):
    """State maintained throughout agent execution"""
    messages: Annotated[List, operator.add]
    user_id: str
    conversation_id: str
    current_intent: Optional[str]
    tools_called: List[str]
    execution_start: datetime
    error: Optional[str]


# ============================================================================
# System Prompts
# ============================================================================

SYSTEM_PROMPT = """You are an AI DevOps assistant that helps users manage their infrastructure and applications through natural language commands.

You have access to tools that connect to 6 integrated projects:

**Project 1 - MCP AWS Server (AWS Operations):**
- ec2_list_instances: List EC2 instances with filters
- ec2_start_instance: Start a stopped EC2 instance
- ec2_stop_instance: Stop a running EC2 instance
- rds_describe_instance: Get RDS database details
- cloudwatch_get_metrics: Query CloudWatch metrics

**Project 3 - K8s AgentOps (Kubernetes):**
- k8s_list_agents: List deployed AI agents
- k8s_deploy_agent: Deploy a new AI agent
- k8s_scale_agent: Scale agent replicas

**Project 4 - CI/CD Framework (Deployments):**
- trigger_deployment: Deploy a service to an environment
- rollback_deployment: Rollback a failed deployment

**Project 5 - Logging & Threat Analytics (SIEM):**
- search_logs: Search application logs
- query_threats: Query security alerts

**Project 6 - Observability Fabric (Monitoring):**
- get_metrics: Query Prometheus metrics (PromQL)
- query_traces: Search distributed traces

## Guidelines:

1. **Understand Intent**: Parse the user's request to identify what they want to accomplish.

2. **Select Tools**: Choose the appropriate tool(s) from the available projects.

3. **Execute Carefully**: For destructive operations (stop, delete, rollback), confirm with the user first.

4. **Provide Context**: Explain what you're doing and why.

5. **Handle Errors**: If a tool fails, explain the error and suggest alternatives.

6. **Multi-Step Tasks**: For complex requests, break them into steps and execute sequentially.

## Examples:

User: "Show me all production EC2 instances"
→ Use ec2_list_instances with filters for Environment=production

User: "Deploy auth-service to staging"
→ Use trigger_deployment with service=auth-service, environment=staging

User: "Why is my API slow?"
→ 1. Use get_metrics to check latency
   2. Use search_logs to find errors
   3. Use rds_describe_instance if database-related

User: "Scale the analytics agent to 5 replicas"
→ Use k8s_scale_agent with name=analytics, replicas=5

Always be helpful, accurate, and security-conscious. Never expose sensitive data like passwords or API keys in responses.
"""


# ============================================================================
# LLM Configuration
# ============================================================================

def get_llm():
    """Get the configured LLM (routes through Project 2 Security Gateway)"""
    if settings.LLM_PROVIDER == "anthropic":
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            base_url=f"{settings.LLM_GATEWAY_URL}/v1",  # Route through gateway
            temperature=0.1,
            max_tokens=4096,
        )
    else:
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=f"{settings.LLM_GATEWAY_URL}/v1",  # Route through gateway
            temperature=0.1,
            max_tokens=4096,
        )


# ============================================================================
# Agent Nodes
# ============================================================================

def create_agent_node():
    """Create the main agent reasoning node"""

    llm = get_llm()
    tools = tool_registry.get_all_tools()
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm_with_tools

    async def agent_node(state: AgentState) -> AgentState:
        """Main agent reasoning"""
        logger.info(f"Agent node processing for user {state['user_id']}")

        try:
            response = await chain.ainvoke({"messages": state["messages"]})

            return {
                "messages": [response],
                "error": None,
            }
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return {
                "messages": [AIMessage(content=f"I encountered an error: {str(e)}")],
                "error": str(e),
            }

    return agent_node


def create_tool_node():
    """Create the tool execution node"""
    tools = tool_registry.get_all_tools()
    return ToolNode(tools)


# ============================================================================
# Routing Logic
# ============================================================================

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determine if we should continue to tools or end"""
    messages = state["messages"]

    if not messages:
        return "end"

    last_message = messages[-1]

    # Check if the last message has tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"Routing to tools: {[tc['name'] for tc in last_message.tool_calls]}")
        return "tools"

    return "end"


# ============================================================================
# Graph Construction
# ============================================================================

def create_agent_graph():
    """Create the LangGraph agent workflow"""

    # Create state graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", create_agent_node())
    workflow.add_node("tools", create_tool_node())

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )

    # After tools, go back to agent
    workflow.add_edge("tools", "agent")

    # Compile with memory for conversation persistence
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    logger.info("Agent graph compiled successfully")
    return graph


# ============================================================================
# Agent Executor
# ============================================================================

class AgentExecutor:
    """
    High-level agent executor with conversation management.

    Handles:
    - Conversation state
    - Execution tracking
    - Error handling
    - Response formatting
    """

    def __init__(self):
        self.graph = create_agent_graph()
        logger.info("AgentExecutor initialized")

    async def run(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
    ) -> dict:
        """
        Execute agent for a user message.

        Args:
            message: User's natural language input
            user_id: User identifier
            conversation_id: Conversation/session ID

        Returns:
            dict with response, tools_used, execution_time, etc.
        """
        start_time = datetime.now(UTC)
        logger.info(f"Executing agent for user={user_id}, conv={conversation_id}")

        try:
            # Prepare initial state
            initial_state: AgentState = {
                "messages": [HumanMessage(content=message)],
                "user_id": user_id,
                "conversation_id": conversation_id,
                "current_intent": None,
                "tools_called": [],
                "execution_start": start_time,
                "error": None,
            }

            # Configure with conversation ID for memory
            config = {
                "configurable": {
                    "thread_id": conversation_id,
                }
            }

            # Execute graph
            final_state = await self.graph.ainvoke(initial_state, config)

            # Extract response
            messages = final_state.get("messages", [])
            response_content = ""
            tools_used = []

            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.content:
                        response_content = msg.content
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        tools_used.extend([tc["name"] for tc in msg.tool_calls])

            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            return {
                "message": response_content or "I processed your request.",
                "conversation_id": conversation_id,
                "tools_used": list(set(tools_used)),
                "execution_time_ms": execution_time_ms,
                "error": final_state.get("error"),
            }

        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            execution_time_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

            return {
                "message": f"I encountered an error processing your request: {str(e)}",
                "conversation_id": conversation_id,
                "tools_used": [],
                "execution_time_ms": execution_time_ms,
                "error": str(e),
            }

    async def stream(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
    ):
        """
        Stream agent execution for real-time updates.

        Yields status updates and chunks as the agent processes.
        """
        start_time = datetime.now(UTC)

        initial_state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "conversation_id": conversation_id,
            "current_intent": None,
            "tools_called": [],
            "execution_start": start_time,
            "error": None,
        }

        config = {
            "configurable": {
                "thread_id": conversation_id,
            }
        }

        try:
            async for event in self.graph.astream(initial_state, config):
                for node_name, node_output in event.items():
                    yield {
                        "type": "node",
                        "node": node_name,
                        "output": node_output,
                    }

            yield {
                "type": "complete",
                "execution_time_ms": int((datetime.now(UTC) - start_time).total_seconds() * 1000),
            }

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }


# Global executor instance
agent_executor = AgentExecutor()
