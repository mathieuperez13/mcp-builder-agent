from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from agents.lifecycle import AgentHooks
from agents.run_context import RunContextWrapper, TContext
from agents.tool import Tool

from .server_registry import ensure_mcp_server_registry_in_context

if TYPE_CHECKING:
    from .agent import Agent


class MCPAgentHooks(AgentHooks, Generic[TContext]):  # type: ignore[misc]
    """
    Agent hooks for MCP agents. This class acts as a passthrough for any existing hooks, while
    also loading MCP tools on agent start.
    """

    def __init__(self, agent: Agent, original_hooks: AgentHooks[TContext] | None = None) -> None:
        self.original_hooks = original_hooks
        self.agent = agent

    async def on_start(self, context: RunContextWrapper[TContext], agent: Agent) -> None:
        # First load MCP tools if needed
        if hasattr(self.agent, "mcp_servers") and self.agent.mcp_servers:
            # Ensure MCP server registry is in context
            ensure_mcp_server_registry_in_context(context)

            # Load MCP tools
            await self.agent.load_mcp_tools(context)

        # Then call the original hooks if they exist
        if self.original_hooks:
            await self.original_hooks.on_start(context, agent)

    async def on_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        output: Any,
    ) -> None:
        if self.original_hooks:
            await self.original_hooks.on_end(context, agent, output)

    async def on_handoff(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        source: Agent,
    ) -> None:
        if self.original_hooks:
            await self.original_hooks.on_handoff(context, agent, source)

    async def on_tool_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        tool: Tool,
    ) -> None:
        if self.original_hooks:
            await self.original_hooks.on_tool_start(context, agent, tool)

    async def on_tool_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        tool: Tool,
        result: str,
    ) -> None:
        if self.original_hooks:
            await self.original_hooks.on_tool_end(context, agent, tool, result)
