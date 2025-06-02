"""Logger for the MCP extension."""

import logging

# Use the same logger as the base package if available, otherwise create our own
try:
    from agents.logger import logger
except ImportError:
    # Create a logger for the mcp_agent package
    logger = logging.getLogger("openai.agents.mcp")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

__all__ = ["logger"]
