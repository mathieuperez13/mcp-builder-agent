import asyncio
import json
import os
from linkup import LinkupClient # Official Linkup SDK
from .config import LINKUP_API_KEY

# Le nom de la variable d'environnement est géré dans config.py maintenant
# EXPECTED_LINKUP_API_KEY_ENV_NAME = "LINKUP_API_KEY"

async def search_with_linkup(query: str, depth: str = "standard", output_type: str = "searchResults") -> str:
    """
    Performs a web search using the Linkup Python client.

    Args:
        query: The search query.
        depth: The search depth (e.g., "basic", "standard", "deep"). Defaults to "standard".
        output_type: The output type (e.g., "answer", "searchResults"). Defaults to "searchResults".

    Returns:
        A string containing the search results (or an error message in JSON format).
    """
    if not LINKUP_API_KEY:
        error_msg = "Error: Linkup API key is not configured. Check your .env file and config.py."
        print(f"[LinkupService] CRITICAL ERROR: {error_msg}")
        return json.dumps({"error": error_msg})

    try:
        print(f"[LinkupService] Initializing LinkupClient.")
        client = LinkupClient(api_key=LINKUP_API_KEY)

        print(f"[LinkupService] Sending query to Linkup SDK (asynchronous via to_thread): '{query}'")

        # Execute the synchronous client.search method in a separate thread
        # to avoid blocking the asyncio event loop.
        response = await asyncio.to_thread(
            client.search,  # The synchronous function to call
            query=query,    # Arguments for client.search
            depth=depth,
            output_type=output_type,
            include_images=False # Can be parameterized if needed
        )

        print(f"[LinkupService] Received response from Linkup SDK.")

        if response:
            # The Linkup SDK returns a Pydantic object (LinkupAnswer or LinkupSearchResults).
            # We convert it to a JSON string for the agent's tool.
            try:
                if hasattr(response, 'model_dump_json'): # Pydantic v2+
                    return response.model_dump_json(indent=2)
                elif hasattr(response, 'json'): # Pydantic v1 (often .json() not .dict() for direct JSON serialization)
                    return response.json(indent=2)
                elif hasattr(response, 'dict'): # Fallback for Pydantic v1
                    return json.dumps(response.dict(), indent=2)
                elif isinstance(response, str):
                    return response # If it's already a JSON string
                else:
                    # Generic serialization attempt, less likely to be correct for Pydantic
                    print(f"[LinkupService] Warning: Unexpected response type from Linkup SDK: {type(response)}. Attempting direct json.dumps.")
                    return json.dumps(response, indent=2, default=str) # default=str to handle non-serializable types
            except Exception as serialization_error:
                print(f"[LinkupService] Error: Could not serialize Linkup SDK response: {serialization_error}")
                return json.dumps({"error": f"Linkup SDK response could not be serialized. Response type: {type(response)}"})
        else:
            print("[LinkupService] Linkup SDK returned an empty or null response.")
            return json.dumps({"info": "Linkup SDK returned an empty or null response."})

    except ImportError:
        critical_error_msg = "Error: The 'linkup' library for Linkup search is not installed."
        print(f"[LinkupService] CRITICAL ERROR: {critical_error_msg}")
        return json.dumps({"error": critical_error_msg})
    except Exception as e:
        detailed_error_msg = f"Error during Linkup SDK operation: {str(e)} (Type: {type(e).__name__})"
        print(f"[LinkupService] {detailed_error_msg}")
        # Attempt to extract more info if it's a Linkup API related exception
        if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
            detailed_error_msg += f" - Linkup Response Details: {e.response.text}"
        return json.dumps({"error": detailed_error_msg})

if __name__ == '__main__':
    # Test section for the Linkup service
    async def test_linkup_search():
        print("Testing Linkup service...")
        if not LINKUP_API_KEY:
            print("ERROR: LINKUP_API_KEY is not set. Please configure it in your .env file.")
            return

        test_query = "What is LangChain?"
        results = await search_with_linkup(test_query)
        print(f"\nResults for query '{test_query}':")
        try:
            # Try to parse JSON for cleaner display
            parsed_results = json.loads(results)
            print(json.dumps(parsed_results, indent=2))
        except json.JSONDecodeError:
            print(results) # If not valid JSON, print as is
        
        # test_query_error = ""
        # results_error = await search_with_linkup(test_query_error) # Test an error case if relevant
        # print(f"\nResults for empty query: {results_error}")

    asyncio.run(test_linkup_search()) 