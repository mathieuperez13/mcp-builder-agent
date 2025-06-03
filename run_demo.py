import asyncio, json, sys
import logging
from dotenv import load_dotenv
from orchestrator.orchestrator import create_orchestrator
from agents import Runner

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mcp_builder.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("=== REAL MCP Builder Agent Demo Started ===")
    
    user_request = sys.argv[1] if len(sys.argv) > 1 else input("prompt: ")
    logger.info(f"User request received: '{user_request}'")
    
    try:
        logger.info("Creating Orchestrator with connected MCP servers...")
        orchestrator = await create_orchestrator()
        
        logger.info("Starting REAL agent orchestration with Orchestrator...")
        result = await Runner.run(orchestrator, user_request, max_turns=25)
        
        logger.info("REAL agent orchestration completed successfully")
        logger.info(f"Final result: {result.final_output}")
        
        print(json.dumps(result.final_output, indent=2))
        
    except Exception as e:
        logger.error(f"Error during REAL execution: {str(e)}", exc_info=True)
        raise
    
    logger.info("=== REAL MCP Builder Agent Demo Completed ===")

if __name__ == "__main__":
    asyncio.run(main())

