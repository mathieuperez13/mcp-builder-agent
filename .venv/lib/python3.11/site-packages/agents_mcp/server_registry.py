"""Functions for managing MCP server registry."""

from typing import Any, Optional, cast

from agents.run_context import RunContextWrapper, TContext
from mcp_agent.config import MCPSettings, Settings, get_settings
from mcp_agent.mcp_server_registry import ServerRegistry

from agents_mcp.logger import logger


def load_mcp_server_registry(
    config: MCPSettings | None = None, config_path: str | None = None
) -> ServerRegistry:
    """
    Load MCP server registry from config object or config file path.

    Args:
        config: The MCPSettings object containing the server configurations.
            If unspecified, it will be loaded from the config_path.
        config_path: The file path to load the MCP server configurations from.
            if config is unspecified, this is required.
    """
    try:
        settings: Optional[Settings] = None
        if config:
            # Use provided settings object
            logger.debug("Loading MCP server registry from provided MCPSettings object.")
            settings = Settings(mcp=config)
        else:
            # Load settings from config file
            logger.debug("Loading MCP server registry from config file: %s", config_path)
            settings = get_settings(config_path)

        # Create the ServerRegistry instance
        server_registry = ServerRegistry(config=settings)
        return server_registry
    except Exception as e:
        logger.error(
            "Error loading MCP server registry. config=%s, config_path=%s, Error: %s",
            config.model_dump_json() if config else "None",
            config_path,
            e,
        )
        raise


def ensure_mcp_server_registry_in_context(
    run_context: RunContextWrapper[TContext], force: bool = False
) -> ServerRegistry:
    """
    Load the MCP server registry and attach it to the context object.
    If the server registry is already loaded, it will be returned.

    Args:
        run_context: Run context wrapper which will have the server registry attached
        force: Whether to force reload the server registry
    """
    # Check if server registry is already loaded
    context_obj = cast(Any, run_context.context)
    server_registry = getattr(context_obj, "mcp_server_registry", None)
    if not force and server_registry:
        logger.debug("MCP server registry already loaded in context. Skipping reload.")
        return cast(ServerRegistry, server_registry)

    # Load the server registry
    config = getattr(context_obj, "mcp_config", None)
    config_path = getattr(context_obj, "mcp_config_path", None)
    server_registry = load_mcp_server_registry(config=config, config_path=config_path)

    # Attach the server registry to the context
    context_obj.mcp_server_registry = server_registry

    return server_registry
