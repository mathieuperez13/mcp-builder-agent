from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Generic

from agents import Agent as BaseAgent
from agents.items import ItemHelpers
from agents.run_context import RunContextWrapper, TContext
from agents.tool import Tool, function_tool
from agents.util import _transforms

from .agent_hooks import MCPAgentHooks
from .aggregator import initialize_mcp_aggregator
from .logger import logger
from .server_registry import ensure_mcp_server_registry_in_context
from .tools import mcp_list_tools

if TYPE_CHECKING:
    from agents.result import RunResult
    from mcp_agent.mcp.mcp_aggregator import MCPAggregator
    from mcp_agent.mcp_server_registry import ServerRegistry


@dataclass
class Agent(BaseAgent, Generic[TContext]):  # type: ignore[misc]
    """
    Extends the OpenAI Agent SDK's Agent class with MCP support.

    This class adds the ability to connect to Model Context Protocol (MCP) servers
    and use their tools alongside native OpenAI Agent SDK tools.

    Example usage:
    ```python
    from mcp_agent import Agent

    agent = Agent(
        name="MCP Assistant",
        instructions="You are a helpful assistant.",
        tools=[existing_tools_still_work],
        mcp_servers=["fetch", "filesystem"]
    )
    ```
    """

    mcp_servers: list[str] = field(default_factory=list)
    """A list of MCP server names to use with this agent.

    The agent will automatically discover and include tools from these MCP servers.
    Each server name must be registered in the server registry,
    which is initialized from mcp_agent.config.yaml.
    """

    mcp_server_registry: ServerRegistry | None = None
    """The server registry to use with this agent.
    If not provided, it will be loaded from the run context,
    which initializes it from mcp_agent.config.yaml.
    """

    _openai_tools: list[Tool] = field(default_factory=list)
    """A list of OpenAI tools that the agent can use.
    This maps to any tools set in the "tools" field in the Agent constructor"""

    _mcp_tools: list[Tool] = field(default_factory=list)
    """List of tools loaded from MCP servers."""

    _mcp_aggregator: MCPAggregator | None = None
    """The MCP aggregator used by this agent. Will be created lazily when needed."""

    _mcp_initialized: bool = False
    """Whether MCP tools have been loaded for this agent."""

    def __post_init__(self):
        self._openai_tools = self.tools

        # Create a wrapper around the original hooks to inject MCP tool loading
        self._original_hooks = self.hooks
        self.hooks: MCPAgentHooks = MCPAgentHooks(agent=self, original_hooks=self._original_hooks)

    async def load_mcp_tools(
        self, run_context: RunContextWrapper[TContext], force: bool = False
    ) -> None:
        """Load tools from MCP servers and add them to this agent's tools."""

        logger.debug(f"MCP servers: {self.mcp_servers}")

        if not self.mcp_servers:
            logger.debug(
                f"No MCP servers specified for agent {self.name}, skipping MCP tool loading"
            )
            return
        elif self._mcp_initialized and not force:
            logger.debug(f"MCP tools already loaded for agent {self.name}, skipping reload")
            return

        # Ensure MCP server registry is in context
        ensure_mcp_server_registry_in_context(run_context)

        if self._mcp_aggregator is None or force:
            self._mcp_aggregator = await initialize_mcp_aggregator(
                run_context,
                name=self.name,
                servers=self.mcp_servers,
                server_registry=self.mcp_server_registry,
                connection_persistence=True,
            )

        # Get all tools from the MCP servers
        mcp_tools = await mcp_list_tools(self._mcp_aggregator)

        # Store the MCP tools in a separate list
        logger.info(f"Adding {len(mcp_tools)} MCP tools to agent {self.name}")
        self._mcp_tools = mcp_tools
        self.tools = self._openai_tools + self._mcp_tools
        self._mcp_initialized = True

    async def cleanup_resources(self) -> None:
        """Clean up resources when the agent is done."""
        # First call the parent class's cleanup_resources if it exists
        parent_cleanup = getattr(super(), "cleanup_resources", None)
        if parent_cleanup and callable(parent_cleanup):
            await parent_cleanup()

        if self._mcp_aggregator:
            logger.info(f"Cleaning up MCP resources for agent {self.name}")
            try:
                await self._mcp_aggregator.__aexit__(None, None, None)
                self._mcp_aggregator = None
                self._mcp_initialized = False
                self._mcp_tools = []
            except Exception as e:
                logger.error(f"Error cleaning up MCP resources for agent {self.name}: {e}")

    def as_tool(
        self,
        tool_name: str | None,
        tool_description: str | None,
        custom_output_extractor: Callable[[RunResult], Awaitable[str]] | None = None,
    ) -> Tool:
        """Transform this agent into a tool, callable by other agents.

        This is different from handoffs in two ways:
        1. In handoffs, the new agent receives the conversation history. In this tool, the new agent
           receives generated input.
        2. In handoffs, the new agent takes over the conversation. In this tool, the new agent is
           called as a tool, and the conversation is continued by the original agent.

        Args:
            tool_name: The name of the tool. If not provided, the agent's name will be used.
            tool_description: The description of the tool, which should indicate what it does and
                when to use it.
            custom_output_extractor: A function that extracts the output from the agent. If not
                provided, the last message from the agent will be used.
        """

        @function_tool(
            name_override=tool_name or _transforms.transform_string_function_style(self.name),
            description_override=tool_description or "",
        )
        async def run_agent(context: RunContextWrapper, input: str) -> str:
            from agents.run import Runner

            if self.mcp_servers:
                # Ensure MCP server registry is in context
                ensure_mcp_server_registry_in_context(context)

                # Load MCP tools
                await self.load_mcp_tools(context)

            output = await Runner.run(
                starting_agent=self,
                input=input,
                context=context.context,
            )
            if custom_output_extractor:
                return await custom_output_extractor(output)

            return ItemHelpers.text_message_outputs(output.new_items)  # type: ignore # We know this returns a string

        return run_agent
