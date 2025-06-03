import asyncio
import json
import os
import logging
from dotenv import load_dotenv
from agents import Agent, function_tool
import httpx

# Optional import for LitellmModel to handle compatibility issues
try:
    from agents.extensions.models.litellm_model import LitellmModel
    LITELLM_AVAILABLE = True
except Exception as e:
    print(f"Warning: LitellmModel not available: {e}. Using default OpenAI model.")
    LitellmModel = None
    LITELLM_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configuration
LINKUP_API_KEY = os.getenv("LINKUP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-opus-4-20250514")

logger = logging.getLogger(__name__)

async def linkup_search_worker(query: str, depth: str = "standard") -> str:
    """
    Perform deep web search using Linkup API (same implementation as orchestrator).
    
    Args:
        query: The search query string
        depth: Search depth - "standard" or "deep" (default: "deep")
    
    Returns:
        String containing search results with answer and sources
    """
    api_key = LINKUP_API_KEY
    if not api_key:
        logger.error("LINKUP_API_KEY not found in environment variables")
        return "Error: Linkup API key not configured"
    
    base_url = os.getenv("LINKUP_BASE_URL", "https://api.linkup.so")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    depth = "standard"
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
                        formatted_result += f"{i}. {title} - {url}\n"
                
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
async def deep_research_tool(subject: str) -> str:
    """
    Perform comprehensive research on a specific tool/API using multiple targeted searches.
    
    Args:
        subject: The name of the tool/API to research
    
    Returns:
        String containing comprehensive research results in JSON format
    """
    if not LINKUP_API_KEY:
        logger.error("LINKUP_API_KEY not configured")
        return json.dumps({"error": "Linkup API key not configured"})

    logger.info(f"Starting deep research for: {subject}")
    
    # Define search categories for comprehensive research
    search_categories = {
        "general_info": f"what is {subject} API overview technology description",
        "github_repository": f"{subject} official GitHub repository source code",
        "documentation": f"{subject} official API documentation developer docs",
        "release_info": f"{subject} release date launch date version history",
        "community_feedback": f"site:reddit.com {subject} API pros cons review experience",
        "use_cases": f"{subject} API use cases examples projects tutorials github",
        "compatibility": f"{subject} API stack compatibility python javascript integration",
        "pricing": f"{subject} API pricing free tier business model cost",
        "security": f"{subject} API security SOC compliance data policy",
        "mcp_integration": f"{subject} Model Context Protocol MCP integration"
    }

    try:
        # Perform all searches concurrently using the direct linkup search function
        tasks = []
        for category, query in search_categories.items():
            task = linkup_search_worker(query, depth="deep")
            tasks.append(task)
        
        logger.info(f"Executing {len(tasks)} research queries for {subject}")
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process and aggregate results
        aggregated_data = {}
        category_keys = list(search_categories.keys())
        
        for i, result in enumerate(search_results):
            category = category_keys[i]
            if isinstance(result, Exception):
                logger.error(f"Error in {category} search: {result}")
                aggregated_data[category] = {"error": str(result)}
            else:
                aggregated_data[category] = {"search_result": result}
        
        logger.info(f"Research completed for {subject}")
        return json.dumps(aggregated_data, indent=2)
        
    except Exception as e:
        logger.error(f"Research failed for {subject}: {e}")
        return json.dumps({"error": f"Research failed: {str(e)}"})

# Worker prompt for deep research
worker_prompt = """
# Deep Research Specialist for Tool Analysis

You are an expert research agent specialized in comprehensive analysis of developer tools and APIs. Your mission is to conduct thorough research and provide structured analysis.

## Your Process

1. **Use the deep_research_tool** to gather comprehensive information about the assigned tool
2. **Analyze and synthesize** the research data from multiple sources
3. **Extract key information** focusing on developer needs and implementation details
4. **Format your findings** into the required JSON structure

## Required Output Format

You MUST output your findings in this exact JSON structure:

```json
{
  "Titre": "Name of the tool/API researched",
  "subtitle": "A short descriptive sentence about the product/API",
  "Github link": "Link to the official GitHub repository (if found, otherwise null)",
  "Doc link": "Link to the official documentation (if found, otherwise null)",
  "release date": "Release date of the tool/API (if found, otherwise null)",
  "stack compatility tag": ["tag1", "tag2"],
  "use case": [ 
    {
      "description": "Description of the use case", 
      "repository_info": {
        "link": "Link to an example GitHub repository (must have a link)",
        "type": "officiel" 
      } 
    }
  ],
  "pros": ["Pro 1 from community discussions (e.g., Reddit)", "Pro 2"],
  "cons": ["Con 1 from community discussions (e.g., Reddit)", "Con 2"],
  "pricing/business model": "Description of pricing or business model (if found, otherwise null)",
  "security informations": "Security details like SOC II compliance, data security policies (if found, otherwise null)",
  "MCP_link": "Link to the Model Context Protocol (official or community, if found, otherwise null)"
}
```

## Critical Instructions

- **Output ONLY the JSON object** - no explanations, markdown, or conversational text
- **Focus on developer-relevant information** from the research data
- **Prioritize community feedback** (Reddit, forums) for pros/cons
- **Use null for missing information** - do not guess or make up data
- **Ensure use cases have GitHub repository links** - discard those without links
- **Mark repository type** as "officiel" (official) or "communauté" (community)

Start your research immediately using the deep_research_tool.
"""

def create_worker_agent() -> Agent:
    """
    Create a worker agent for deep research on a specific tool.
    
    Args:
        tool_name: The name of the tool/API to research
    
    Returns:
        Agent: Configured worker agent for deep research
    """
    logger.info(f"Creating worker agent for worker agent")
    
    # Configure LLM model
    llm_model = None
    
    if LITELLM_AVAILABLE and ANTHROPIC_API_KEY and CLAUDE_MODEL_NAME:
        try:
            llm_model = LitellmModel(model=CLAUDE_MODEL_NAME)
            logger.info(f"Using Claude model: {CLAUDE_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Claude configuration failed: {e}")
            llm_model = None
    
    if not llm_model and OPENAI_API_KEY:
        logger.info("Using default OpenAI model")
        llm_model = None
    elif not llm_model:
        logger.warning("No LLM API key configured")
    
    # Create personalized prompt
    personalized_prompt = worker_prompt + f"\n\nYour assigned tool for research: \n\nBegin research immediately."
    
    worker = Agent(
        name="worker",
        model=llm_model,
        instructions=personalized_prompt,
        tools=[deep_research_tool]
    )
    
    logger.info(f"Worker agent created for worker agent")
    return worker 