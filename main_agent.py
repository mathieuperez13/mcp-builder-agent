import asyncio
import os
import json
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from agent_tools import LinkupSearchTool
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, LINKUP_API_KEY, CLAUDE_MODEL_NAME

def run_deep_search_agent():
    """
    Configures and runs the deep search agent.
    """
    print("Initializing deep search agent...")

    if not LINKUP_API_KEY:
        print("CRITICAL: LINKUP_API_KEY is not configured. The agent will not be able to use its main tool.")

    llm_model = None  # Default initialization

    # Configure LLM Model
    if ANTHROPIC_API_KEY and CLAUDE_MODEL_NAME:
        print(f"Configuring LiteLLM with Claude model: {CLAUDE_MODEL_NAME}")
        try:
            llm_model = LitellmModel(
                model=CLAUDE_MODEL_NAME,
                # api_key=ANTHROPIC_API_KEY # LiteLLM should pick up ANTHROPIC_API_KEY from env automatically if named so.
                                         # Otherwise, uncomment this line.
            )
            print(f"LiteLLM model ({CLAUDE_MODEL_NAME}) configured.")
        except Exception as e:
            print(f"ERROR during LiteLLM configuration for Claude: {e}")
            print("Verify that LiteLLM is installed (`pip install litellm`) and the model name is correct.")
            print("Falling back to default OpenAI model if OPENAI_API_KEY is available.")
            llm_model = None # Reset on failure

    if not llm_model and OPENAI_API_KEY:
        print("Configuring with default OpenAI model (requires OPENAI_API_KEY).")
        # To use the default OpenAI model, do not pass `model` or pass `None`
        # The Agent will use the default OpenAI client if OPENAI_API_KEY is in the env.
        llm_model = None # Explicitly None to use OpenAI default
    elif not llm_model:
        print("WARNING: No LLM API key (OPENAI_API_KEY or ANTHROPIC_API_KEY for Claude) is defined or model could not be loaded.")
        print("The agent might not function correctly without a configured LLM.")
        # return # You might want to exit if no model is usable

    linkup_tool = LinkupSearchTool()

    deep_search_agent = Agent(
        name="DeepSearchAgent",
        instructions=(
            "You are an intelligent deep search agent. Your primary goal is to find information about a specific technology company and its API. "
            "When a user provides a topic, use the 'LinkupDeepSearch' tool to gather detailed information. "
            "The topic will be given to you in the user's message. You must extract this topic and pass it to the 'LinkupDeepSearch' tool. "
            "The tool will return a JSON string containing search results for various categories. "
            "If the search results contain multiple entities for the given topic, you MUST focus SOLELY on the technology company that offers an API. Disregard other types of entities (e.g., games, books, etc.). "
            "Your final task is to synthesize the gathered information for the technology company/API into a single, valid JSON object, including any Model Context Protocol (MCP) information found. "
            "The JSON output MUST strictly follow this structure:\\n"
            # Start of the JSON template using triple quotes
            '''{
  "Titre": "Name of the tool/API researched",
  "subtitle": "A short descriptive sentence about the product/API",
  "Github link": "Link to the official GitHub repository (if found, otherwise null)",
  "Lien de la doc": "Link to the official documentation (if found, otherwise null)",
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
  "MCP_link": "Link to the Model Context Protocol (official or community, if found, otherwise null)"  # New MCP field
}'''
            # End of the JSON template
            "\\nEnsure the output is ONLY the raw JSON object. Do NOT include any conversational text, explanations, or markdown formatting before or after the JSON block. "
            "The entire response must be the JSON object itself, starting with { and ending with }. "
            "For 'pros' and 'cons', prioritize information found on community platforms like Reddit or forums over official statements. "
            "If some information for a field is not found, use null as the value for that field in the JSON. "
            "For fields like 'stack compatility tag', 'pros', and 'cons', if no information is found, use an empty array [] or null. "
            "For the 'use case' field: \n"
            "  - Only include use cases that have an associated GitHub repository link. Discard use cases without a repository link. \n"
            "  - For each use case, the 'repository_info' object must contain a 'link' and a 'type'. \n"
            "  - The 'type' should be \"officiel\" if the GitHub repository seems to be an official example or SDK provided by the searched tool/company itself (e.g., hosted under their official GitHub organization, or clearly labelled as official). \n"
            "  - The 'type' should be \"communauté\" if the GitHub repository is a project, example, or wrapper created by a third-party user or the community. \n"
            "  - If it's unclear whether a repository is official or community, err on the side of marking it \"communauté\"."
        ),
        tools=[linkup_tool],
        model=llm_model # Will be None if Claude fails and OpenAI default is used, or the Claude model instance
    )

    print("Deep search agent initialized.")
    if llm_model and hasattr(llm_model, 'model') and llm_model.model: # Check if llm_model is not None and has a model attribute
        print(f"Using model: {llm_model.model}")
    elif OPENAI_API_KEY and not (ANTHROPIC_API_KEY and CLAUDE_MODEL_NAME and llm_model) : # If OpenAI is the fallback
        print("Using model: Default OpenAI (via OPENAI_API_KEY)")
    elif not llm_model:
        print("No LLM could be configured. The agent will run without a specific model assigned at initialization.")

    target_subject = input("What topic do you want to research in depth? (e.g., OpenAI API, LangChain, FastAPI, etc.) ")

    if not target_subject:
        print("No topic provided. Exiting.")
        return

    print(f"Starting research on: {target_subject}")
    
    initial_prompt = f"Perform an in-depth search on the following topic: '{target_subject}'."

    print("Running agent (this may take some time, especially with multiple Linkup searches)...")
    try:
        # Runner.run_sync can execute agents with asynchronous tools.
        # The SDK handles the event loop for asynchronous tool calls.
        result = Runner.run_sync(deep_search_agent, initial_prompt)

        print("\n--- Agent Final Output ---")
        if result.final_output:
            print(result.final_output) # Should be a Markdown formatted string
        else:
            print("The agent did not produce an explicit final output.")
            print(f"  Final execution status: {result.status}")
            if result.error:
                print(f"  Error encountered: {result.error}")
            # For debugging, you can inspect result.run_state.items
            # print("  Execution steps (RunState items):")
            # for item in result.run_state.items:
            #     print(f"    - Type: {item.type}, Content: {str(item.content)[:200]}...") # Print a summary
            #     if hasattr(item, 'tool_name') and item.tool_name:
            #         print(f"      Tool: {item.tool_name}")
            #     if hasattr(item, 'tool_input') and item.tool_input:
            #         print(f"      Tool Input: {item.tool_input}")
            #     if hasattr(item, 'tool_output') and item.tool_output:
            #         output_summary = str(item.tool_output)[:500] + "..." if len(str(item.tool_output)) > 500 else str(item.tool_output)
            #         print(f"      Tool Output (summary): {output_summary}")

    except Exception as e:
        print(f"A major error occurred while running the agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Since run_deep_search_agent is not defined as `async def` currently
    # and Runner.run_sync is used, it can be called directly.
    run_deep_search_agent() 