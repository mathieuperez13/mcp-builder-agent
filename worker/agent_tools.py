import asyncio
import json
from agents.tool import FunctionTool # from openai-agents SDK
from .linkup_service import search_with_linkup # Our asynchronous service
from .config import LINKUP_API_KEY # Ensure LINKUP_API_KEY is available for the test

class LinkupSearchTool(FunctionTool):
    def __init__(self):
        subject_param_schema = {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "The name of the API, tool, or technology to research.",
                }
            },
            "required": ["subject"],
        }
        super().__init__(
            name="LinkupDeepSearch",
            description="Performs in-depth internet searches via the Linkup API to find detailed information on a given subject (API, tool, technology).",
            params_json_schema=subject_param_schema,
            on_invoke_tool=self.run
            # For asynchronous tools, the agent SDK expects an `async def run(self, ...)` method
            # or handles the call to `__call__` in an asyncio task if it's an `async def __call__`.
            # Assuming `async def __call__` is supported or the runner handles the await:
        )

    # The tool's call method must be asynchronous if it uses `await` functions
    async def run(self, _context, subject_json_string: str, _extra_arg=None) -> str: # Renamed subject to subject_json_string for clarity
        """
        The subject_json_string is the name of the API, tool, or technology to research, passed as a JSON string like '{"subject": "ActualTopic"}'.
        This method will orchestrate multiple calls to search_with_linkup
        to collect all requested information and return it as a JSON string.
        """
        try:
            parsed_args = json.loads(subject_json_string)
            subject = parsed_args.get("subject")
            if not subject:
                print(f"[LinkupSearchTool] Error: 'subject' key not found or is empty in parsed JSON: {subject_json_string}")
                return json.dumps({"error": "Invalid subject format received by tool", "details": "Subject key missing after JSON parse."})
        except json.JSONDecodeError:
            # Fallback: if it's not a JSON string, maybe it's already the plain subject string (e.g. if SDK changes behavior or direct test)
            # This part handles if the input is unexpectedly a plain string already.
            # Given the logs, this fallback might not be hit during agent runs, but good for robustness.
            print(f"[LinkupSearchTool] Warning: Could not parse subject_json_string as JSON: '{subject_json_string}'. Using it directly as subject.")
            subject = subject_json_string # Use it as is, assuming it might be the direct subject string.

        if not isinstance(subject, str) or not subject.strip():
             print(f"[LinkupSearchTool] Error: Final subject is not a valid string or is empty: '{subject}'")
             return json.dumps({"error": "Invalid subject after processing", "details": f"Final subject is '{subject}'"})

        print(f"[LinkupSearchTool] Starting deep search for actual subject: {subject}")
        
        # Define search categories to align with the desired JSON output structure
        # and prioritize community sources for pros/cons.
        search_categories = {
            "general_info_and_subtitle": f"what is {subject} API OR {subject} technology overview OR {subject} product description",
            "github_link": f"{subject} official GitHub repository OR {subject} source code link github",
            "documentation_link": f"{subject} official API documentation OR {subject} developer docs",
            "release_date": f"official release date of {subject} API OR {subject} product launch date",
            "reddit_pros_cons_reviews": f"site:reddit.com {subject} API pros and cons OR site:reddit.com {subject} API review OR site:reddit.com {subject} API advantages disadvantages",
            "use_cases_and_examples": f"{subject} API use cases OR projects using {subject} API OR {subject} API tutorial github examples",
            "stack_compatibility": f"{subject} API stack compatibility OR {subject} works with python OR {subject} langchain integration",
            "pricing_business_model": f"{subject} API pricing OR {subject} API free tier OR {subject} API business model",
            "security_information": f"{subject} API security OR {subject} SOC 2 compliance OR {subject} API data policy",
            "mcp_link": f'{subject} Model Context Protocol OR {subject} MCP OR \'Model Context Protocol\' for {subject} API' # New category for MCP
        }

        # Create asyncio tasks for all searches to be performed concurrently
        tasks = []
        for category_key, query_string in search_categories.items():
            # search_with_linkup is already asynchronous
            tasks.append(search_with_linkup(query_string))
        
        print(f"[LinkupSearchTool] Launching {len(tasks)} Linkup queries in parallel for '{subject}'.")
        try:
            search_results_json_strings = await asyncio.gather(*tasks)
        except Exception as e:
            print(f"[LinkupSearchTool] Error during concurrent search execution: {e}")
            return json.dumps({"error": "Error during concurrent Linkup search execution", "details": str(e)})

        print(f"[LinkupSearchTool] All Linkup queries for '{subject}' completed.")

        # Aggregate results
        # Each `result_str` in `search_results_json_strings` is a JSON string
        # returned by `search_with_linkup`.
        aggregated_results = {}
        category_keys = list(search_categories.keys())
        for i, category_key in enumerate(category_keys):
            try:
                # Parse the JSON string to get a Python dictionary
                parsed_result = json.loads(search_results_json_strings[i])
                aggregated_results[category_key] = parsed_result
            except json.JSONDecodeError:
                print(f"[LinkupSearchTool] Error: Could not parse JSON response for category '{category_key}'. Raw response: {search_results_json_strings[i]}")
                aggregated_results[category_key] = {"error": "Invalid JSON response from Linkup", "raw_content": search_results_json_strings[i]}
            except IndexError:
                 print(f"[LinkupSearchTool] Error: Missing result for category '{category_key}'.")
                 aggregated_results[category_key] = {"error": "Missing result from Linkup search."}

        final_json_output = json.dumps(aggregated_results, indent=2)
        # print(f"[LinkupSearchTool] Aggregated results for '{subject}':\n{final_json_output}") # Can be very verbose
        return final_json_output


if __name__ == '__main__':
    # Test section for the LinkupSearchTool
    async def test_tool():
        print("Testing LinkupSearchTool...")
        tool = LinkupSearchTool()
        
        if not LINKUP_API_KEY:
            print("ERROR: LINKUP_API_KEY is not set. Please configure it in your .env file for this test.")
            return

        test_subject = "FastAPI"
        results_json = await tool(test_subject) # Asynchronous call to the tool
        
        print(f"\n--- Final results from LinkupSearchTool for '{test_subject}' ---")
        try:
            parsed_output = json.loads(results_json)
            print(json.dumps(parsed_output, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print("Error: Tool output is not valid JSON.")
            print(results_json)

    asyncio.run(test_tool()) 