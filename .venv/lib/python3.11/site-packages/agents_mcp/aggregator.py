"""Functions for managing MCP server aggregators."""

from agents.run_context import RunContextWrapper, TContext
from mcp_agent.context import Context
from mcp_agent.mcp.mcp_aggregator import MCPAggregator
from mcp_agent.mcp_server_registry import ServerRegistry

from .logger import logger


def create_mcp_aggregator(
    run_context: RunContextWrapper[TContext],
    name: str,
    servers: list[str],
    server_registry: ServerRegistry | None = None,
    connection_persistence: bool = True,
) -> MCPAggregator:
    """
    Create the MCP aggregator with the MCP servers from server registry.
    This doesn't initialize the aggregator. For initialization, use `initialize_mcp_aggregator`.

    Args:
        run_context: Run context wrapper
        name: Name of the agent using the aggregator
        servers: List of MCP server names
        server_registry: Server registry instance
            (if not provided, it will be retrieved from context)
        connection_persistence: Whether to keep the server connections alive, or restart per call
    """
    if not servers:
        raise RuntimeError("No MCP servers specified. No MCP aggregator created.")

    # Get or create the server registry from the context
    context: Context | None = None
    if server_registry:
        context = Context(server_registry=server_registry)
    else:
        server_registry = getattr(run_context.context, "mcp_server_registry", None)
        if not server_registry:
            raise RuntimeError(
                "No server registry found in run context. Either specify it or set in context."
            )
        context = Context(server_registry=server_registry)

    # Create the aggregator
    aggregator = MCPAggregator(
        server_names=servers,
        connection_persistence=connection_persistence,
        name=name,
        context=context,
    )

    return aggregator


async def initialize_mcp_aggregator(
    run_context: RunContextWrapper[TContext],
    name: str,
    servers: list[str],
    server_registry: ServerRegistry | None = None,
    connection_persistence: bool = True,
) -> MCPAggregator:
    """Initialize the MCP aggregator, which initializes all the server connections."""
    # Create the aggregator
    aggregator = create_mcp_aggregator(
        run_context=run_context,
        name=name,
        servers=servers,
        server_registry=server_registry,
        connection_persistence=connection_persistence,
    )

    # Initialize the aggregator
    try:
        logger.info(f"Initializing MCPAggregator for {name} with servers {servers}.")
        await aggregator.__aenter__()
        logger.debug(f"MCPAggregator created and initialized for {name}.")
        return aggregator
    except Exception as e:
        logger.error(f"Error creating MCPAggregator: {e}")
        await aggregator.__aexit__(None, None, None)
        raise
