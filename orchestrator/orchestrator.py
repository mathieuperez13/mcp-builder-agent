import logging
from agents import Agent, handoff, function_tool, ModelSettings
from worker.worker import create_worker_agent

import os, json, asyncio, logging
from agents import Agent, Runner
from agents.mcp.server import MCPServerSse, MCPServerSseParams
import httpx
from typing import Dict, Any, Optional
from .prompts import orch_prompt2, orch_prompt3

logger = logging.getLogger(__name__)


@function_tool
async def linkup_search(query: str, depth: str = "standard") -> str:
    """
    Perform deep web search using Linkup API to find comprehensive information about tools and capabilities.
    
    Args:
        query: The search query string
        depth: Search depth - "standard" or "deep" (default: "deep")
    
    Returns:
        String containing search results with answer and sources
    """
    api_key = os.getenv("LINKUP_API_KEY")
    if not api_key:
        logger.error("LINKUP_API_KEY not found in environment variables")
        return "Error: Linkup API key not configured"
    
    base_url = os.getenv("LINKUP_BASE_URL", "https://api.linkup.so")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    depth = "deep"
    payload = {
        "q": query,
        "depth": depth,
        "outputType": "sourcedAnswer"
    }
    
    try:
        logger.info(f"Performing Linkup search with query: '{query}' and depth: '{depth}'")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/v1/search",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Linkup search completed successfully. Found {len(result.get('sources', []))} sources")
                
                # Format the result as a readable string
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                
                # Create a formatted response
                formatted_result = f"Answer: {answer}\n\n"
                if sources:
                    formatted_result += "Sources:\n"
                    for i, source in enumerate(sources, 1):
                        title = source.get("name", source.get("title", "No title"))
                        url = source.get("url", "No URL")
                        snippet = source.get("snippet", "No snippet")
                        formatted_result += f"{i}. {title} - {url}\n{snippet}\n\n"
                
                logger.info(f"linkup search result: {formatted_result}")
                return formatted_result
            else:
                logger.error(f"Linkup API error: {response.status_code} - {response.text}")
                return f"Error: Linkup API returned status {response.status_code}"
                
    except httpx.TimeoutException:
        logger.error("Linkup API request timed out")
        return "Error: Search request timed out"
    except Exception as e:
        logger.error(f"Error calling Linkup API: {str(e)}")
        return f"Error: Search failed - {str(e)}"

@function_tool
async def research_worker(tool_name: str, research_focus: str = "comprehensive analysis") -> str:
    """
    Deep research worker that can analyze any tool with specific focus areas.
    This tool can be called multiple times in parallel for different tools.
    
    Args:
        tool_name: The name of the tool/API to research
        research_focus: Specific aspect to focus on (e.g., "pricing", "integration", "community feedback")
    
    Returns:
        String containing comprehensive research results in JSON format
    """
    logger.info(f"Starting research for tool: {tool_name} with focus: {research_focus}")
    
    try:
        # Create a worker agent for this specific research task
        worker = create_worker_agent()
        
        # Create research instruction including the tool name and focus
        research_instruction = f"Research the tool/API named '{tool_name}' focusing on {research_focus}. Provide comprehensive analysis including implementation guides, pricing, community feedback, pros/cons, and alternatives."
        
        # Run the worker agent
        runner = Runner()
        result = await runner.run(worker, research_instruction)
        
        logger.info(f"Research completed for {tool_name}")
        return result.final_output if hasattr(result, 'final_output') else str(result)
        
    except Exception as e:
        logger.error(f"Research failed for {tool_name}: {e}")
        return json.dumps({
            "error": f"Research failed for {tool_name}: {str(e)}",
            "tool_name": tool_name,
            "research_focus": research_focus
        })

async def create_orchestrator():
    """Create an Orchestrator agent with linkup to find tools and research_worker for parallel analysis"""
    
    logger.info("Creating Orchestrator agent...")

    orchestrator = Agent(
        name="Orchestrator",
        model="gpt-4o-2024-08-06",
        # model="o3-2025-04-16",
        #model="o4-mini-2025-04-16",
        model_settings=ModelSettings(parallel_tool_calls=True),  # Enable parallel tool calls
        instructions=orch_prompt3,  # Change to orch_prompt for comprehensive search
        handoffs=[],  # No handoffs - using tools instead
        tools=[linkup_search, research_worker]  # Both search and research as parallel tools
    )
    logger.info("Orchestrator agent created successfully with parallel tool calls enabled")
    return orchestrator

# For backwards compatibility
Orchestrator = None

