"""Context class for MCP Agent."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from mcp_agent.config import MCPSettings


@dataclass
class RunnerContext:
    """
    A context class for use with MCP-enabled Agents.

    This dataclass is compliant with the TContext generic parameter in the OpenAI Agent SDK.
    """

    mcp_config: Optional["MCPSettings"] = None
    """Optional MCPSettings object containing the server configurations.
    If unspecified, the MCP settings are loaded from the mcp_config_path."""

    mcp_config_path: Optional[str] = None
    """Optional path to the mcp_agent.config.yaml file.
    If both mcp_config and mcp_config_path are unspecified,
    the default discovery process will look for the config file matching
    "mcp_agent.config.yaml" recursively up from the current working directory."""

    def __init__(
        self,
        mcp_config: Optional["MCPSettings"] = None,
        mcp_config_path: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize the context with MCP settings and any additional attributes.

        Args:
            mcp_config: MCPSettings containing the server configurations.
                If unspecified, the MCP settings are loaded from the mcp_config_path.

            mcp_config_path: Path to the mcp_agent.config.yaml file.
                If both mcp_config and mcp_config_path are unspecified,
                the default discovery process will look for the config file matching
                "mcp_agent.config.yaml" recursively up from the current working directory.
        """
        self.mcp_config = mcp_config
        self.mcp_config_path = mcp_config_path

        # Add any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
