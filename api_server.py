import asyncio
import json
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Imports for the orchestrator logic (same as run_demo.py)
from orchestrator.orchestrator import create_orchestrator
from agents import Runner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent to find apis API",
    description="API for triggering the orchestrator agent to find and research tools based on user queries.",
    version="1.0.0"
)

@app.get("/search/")
async def run_search_agent(question: str = Query(..., description="The user query to search for tools and research them.")):
    """
    Endpoint to run the orchestrator agent with the same logic as run_demo.py.
    Takes a 'question' as URL parameter and returns the orchestrator's analysis.
    """
    logger.info(f"=== API Search Request Started ===")
    logger.info(f"User request received: '{question}'")
    
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="The question cannot be empty.")
    
    try:
        logger.info("Creating Orchestrator with connected MCP servers...")
        orchestrator = await create_orchestrator()
        
        if not orchestrator:
            logger.error("Failed to create orchestrator")
            raise HTTPException(status_code=503, detail={"error": "Service unavailable", "message": "Could not initialize orchestrator."})
        
        logger.info("Starting agent orchestration with Orchestrator...")
        # Using max_turns=25 as in run_demo.py
        result = await Runner.run(orchestrator, question, max_turns=25) 
        
        logger.info("Agent orchestration completed successfully")
        logger.info(f"Final result: {result.final_output}")
        
        # Return as explicit JSON response
        try:
            parsed_json = json.loads(result.final_output)
            return JSONResponse(content=parsed_json)
        except json.JSONDecodeError:
            # If it's not valid JSON, wrap it in a JSON structure
            return JSONResponse(content={"result": result.final_output})

    except Exception as e:
        logger.error(f"Error during API execution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail={"error": "An unexpected error occurred while processing your request.", "details": str(e)}
        )

@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the Agent for API", 
        "description": "Use the /search/ endpoint to query for tools and get comprehensive analysis",
        "example": "/search/?question=I need a tool for image generation"
    }

if __name__ == "__main__":
    logger.info("Starting Uvicorn server for MCP Builder Agent API...")
    # Make sure LINKUP_API_KEY and other environment variables are set
    uvicorn.run(app, host="0.0.0.0", port=8001) 