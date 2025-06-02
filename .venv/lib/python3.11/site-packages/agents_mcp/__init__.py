"""MCP extension for OpenAI Agents SDK.

This package extends the OpenAI Agents SDK to add support for the Model Context Protocol (MCP).
Everything else in the OpenAI Agents SDK will work as expected,
but you can now use tools from MCP servers alongside local tools:

    from agents import Runner
    from agents_mcp import Agent

    agent = Agent(
        name="MCP Assistant",
        tools=[existing_tools_still_work],
        mcp_servers=["fetch", "filesystem"]
    )

    result = await Runner.run(
        starting_agent=agent,
        input="Hello",
        context=Context()
    )
"""

from mcp_agent.config import MCPServerSettings, MCPSettings

from .agent import Agent
from .context import RunnerContext
from .server_registry import (
    ensure_mcp_server_registry_in_context,
    load_mcp_server_registry,
)

__all__ = [
    "Agent",
    "RunnerContext",
    "MCPServerSettings",
    "MCPSettings",
    "ensure_mcp_server_registry_in_context",
    "load_mcp_server_registry",
]
