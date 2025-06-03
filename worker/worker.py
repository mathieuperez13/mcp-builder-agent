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
                        snippet = source.get("snippet", "No snippet")
                        formatted_result += f"{i}. {title} - {url}\n{snippet}\n\n"
                
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
    
    # OLD DETAILED SEARCH CATEGORIES (commented out to reduce API calls)
    # search_categories = {
    #     "general_info": f"what is {subject} API overview technology description",
    #     "github_repository": f"{subject} official GitHub repository source code",
    #     "documentation": f"{subject} official API documentation developer docs",
    #     "release_info": f"{subject} release date launch date version history",
    #     "community_feedback": f"site:reddit.com {subject} API pros cons review experience",
    #     "use_cases": f"{subject} API use cases examples projects tutorials github",
    #     "compatibility": f"{subject} API stack compatibility python javascript integration",
    #     "pricing": f"{subject} API pricing free tier business model cost",
    #     "security": f"{subject} API security SOC compliance data policy",
    #     "mcp_integration": f"{subject} Model Context Protocol MCP integration"
    # }
    
    # NEW CONSOLIDATED SEARCH CATEGORIES (2 searches instead of 10)
    search_categories = {
        "basic_info_technical": f"{subject} API official documentation, GitHub repository stars forks, pricing tiers free tier paid plans business model, release date last update, security SOC2 ISO27001 GDPR compliance, official website logo about description",
        "community_feedback": f"reddit.com {subject} API review pros cons advantages disadvantages experience, OR producthunt.com {subject} featured product launch upvotes ranking, OR stackoverflow.com {subject} API questions tagged discussions development community feedback",
        "implementation_examples": f"{subject} API integration code examples python javascript nodejs curl, SDK libraries installation tutorial, use cases projects GitHub repositories implementations, starter templates getting started guide"
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
# Deep Research Specialist for Comprehensive Tool Analysis

You are an expert research agent specialized in comprehensive analysis of developer tools and APIs. Your mission is to conduct thorough research and provide detailed structured analysis with all community insights, technical details, and integration information.

## Your Process

1. **Use the deep_research_tool** to gather comprehensive information about the assigned tool
2. **Analyze and synthesize** the research data from multiple sources including Reddit, Product Hunt, Stack Overflow
3. **Extract detailed information** focusing on developer needs, community feedback, implementation details, and business information
4. **Format your findings** into the required comprehensive JSON structure

## Required Output Format

You MUST output your findings in this exact JSON structure:

```json
{
  "title": "Extract the official name of the tool/API from research results",
  "subtitle": "Extract a brief descriptive sentence about what the product/API does from documentation or descriptions",
  "logo": "Use the tool name + .png format (e.g., 'openai.png')",
  "logoUrl": "Look for official logo URL in documentation or construct reasonable URL based on tool name",
  "tier_classification": "Classify as 'advanced', 'intermediate', or 'beginner' based on complexity and target audience",
  "githubStars": "Extract the exact number of GitHub stars from repository information (integer, or null if not found)",
  "votes": {
    "up": "Estimate positive community sentiment as integer between 0 and 100 based on Reddit upvotes, positive feedback",
    "down": "Estimate negative community sentiment as integer between 0 and 40 based on Reddit downvotes, negative feedback"
  },
  "relevanceScore": "Assign score 1-100 based on documentation quality, community adoption, GitHub stars, and overall popularity",
  "releaseDate": "Extract the original release/launch date from research results (or null if not found)",
  "lastUpdate": "Extract the most recent update date from GitHub, documentation, or release notes (or null if not found)",
  "pros": [
    "Extract positive points from Reddit discussions, community feedback, and user experiences",
    "Include advantages mentioned in Stack Overflow answers and developer testimonials"
  ],
  "cons": [
    "Extract negative points from Reddit discussions, community complaints, and user experiences", 
    "Include limitations mentioned in Stack Overflow questions and developer feedback"
  ],
  "pricing": {
    "description": "Extract detailed pricing information from official documentation or pricing pages",
    "freeThreshold": "Extract free tier limits (e.g., 'X requests per month', 'Y tokens', etc.) or null",
    "paidRate": "Extract paid pricing rates (e.g., '$X per million tokens', '$Y per month') or null",
    "model": "Extract business model type: 'pay-as-you-go', 'subscription', 'freemium', 'enterprise', etc."
  },
  "community": {
    "peopleInsights": [
      {
        "platform": "Reddit",
        "platformIcon": "https://www.redditstatic.com/shreddit/assets/favicon/64x64.png",
        "title": "Reddit Discussion",
        "upvotes": "Extract or estimate upvotes from Reddit discussions (integer)",
        "description": "Summarize key points from Reddit discussions and community feedback"
      },
      {
        "platform": "Product Hunt",
        "platformIcon": "https://ph-static.imgix.net/ph-logo-1.png", 
        "title": "Product Hunt",
        "badge": "Extract Product Hunt ranking or achievements (e.g., '#1 Product of the Day') or null",
        "description": "Extract Product Hunt launch details, reception, and community response"
      },
      {
        "platform": "Stack Overflow",
        "platformIcon": "https://cdn.sstatic.net/Sites/stackoverflow/Img/favicon.ico",
        "title": "Stack Overflow", 
        "description": "Summarize Stack Overflow discussions, question frequency, and developer community activity"
      }
    ],
    "repositories": [
      {
        "name": "Extract repository names from GitHub search results and examples",
        "author": "Extract GitHub username/organization (format: @username)",
        "link": "Extract official GitHub repository URL from research results",
        "badge": "Mark as 'Official' if from tool's organization, otherwise 'Community'"
      }
    ]
  },
  "integration": {
    "officialResources": [
      {
        "title": "Official Documentation",
        "url": "Extract official documentation URL from research results",
        "type": "documentation"
      },
      {
        "title": "GitHub Repository", 
        "url": "Extract official GitHub repository URL from research results",
        "type": "github"
      }
    ],
    "complianceBadges": [
      {
        "name": "Extract compliance certifications mentioned (SOC2, ISO27001, GDPR, etc.)",
        "color": "Use 'blue' for SOC2, 'green' for ISO27001, 'purple' for GDPR, 'orange' for others"
      }
    ],
    "codeSnippets": {
      "curl": {
        "code": "Create realistic curl command example based on API documentation and examples found",
        "installCommand": null
      },
      "python": {
        "code": "Create realistic Python code example based on SDK documentation and examples found",
        "installCommand": "Extract Python installation command (e.g., 'pip install package-name') from documentation"
      },
      "nodejs": {
        "code": "Create realistic Node.js/JavaScript code example based on SDK documentation and examples found", 
        "installCommand": "Extract Node.js installation command (e.g., 'npm install package-name') from documentation"
      }
    }
  },
  "rank": "Assign ranking 1-10 based on overall quality, popularity, documentation, and community adoption",
  "category": "Extract or infer the API category (e.g., 'AI/ML API', 'Search API', 'Database API', etc.)",
  "tags": ["Extract relevant technology tags from documentation and descriptions (e.g., 'AI', 'OpenAI', 'GPT', 'SDK', 'API')"],
  "useCases": [
    "Extract common use cases mentioned in documentation, examples, and community discussions",
    "Include practical applications found in GitHub repositories and tutorials"
  ]
}
```

## Critical Instructions

- **Output ONLY the JSON object** - no explanations, markdown, or conversational text
- **Focus on community feedback** (Reddit, Product Hunt, Stack Overflow) for pros/cons and insights
- **Extract GitHub stars and community metrics** when available
- **Create realistic code snippets** for curl, Python, and Node.js integration
- **Include multiple repositories** in the community section (aim for 5-10 repositories)
- **Estimate missing metrics** reasonably based on available data (relevanceScore, votes, etc.)
- **Use null for missing information** - do not guess or make up specific data like exact numbers
- **Ensure compliance badges reflect actual security certifications** mentioned in research
- **Prioritize community-sourced pros/cons** over marketing materials

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
        # model=llm_model,
        model="gpt-4o-2024-08-06",
        instructions=personalized_prompt,
        tools=[deep_research_tool]
    )
    
    logger.info(f"Worker agent created for worker agent")
    return worker 