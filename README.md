# MCP Builder Agent

An intelligent agent system that builds Model Context Protocol (MCP) servers by analyzing user requests, finding appropriate tools, and deploying them as accessible endpoints.

## Features

- **Orchestrator Agent**: Analyzes user requests and extracts capabilities
- **Worker Agent**: Searches for tools that match required capabilities  
- **MCP Builder Agent**: Aggregates tools into a unified MCP server

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run the demo:**
   ```bash
   python run_demo.py "I need tools for sending emails and scheduling meetings"
   ```

## Architecture

- `agents/orchestrator.py` - Main coordination agent
- `agents/worker.py` - Tool discovery and evaluation agent  
- `agents/mcp_builder.py` - MCP server generation agent
- `tools/linkup_search.py` - Tool search functionality
- `agents/mcp.py` - MCP server utilities

## Usage

The system takes a natural language request and returns an MCP server URL with the requested capabilities:

```python
import asyncio
from agents.orchestrator import Orchestrator
from agents import Runner

async def main():
    result = await Runner.run_async(Orchestrator, "I need email and calendar tools")
    print(result.final_output)  # {"mcp_url": "...", "summary": "..."}

asyncio.run(main())
```