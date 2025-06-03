import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# API key for Linkup (used by linkup_service.py)
LINKUP_API_KEY = os.getenv("LINKUP_API_KEY")

# API keys for LLM models
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") # For Claude via LiteLLM

# Optional: LiteLLM model name if you want to configure it here
CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-opus-4-20250514") # Example, verify the exact Claude 4 model name you intend to use 