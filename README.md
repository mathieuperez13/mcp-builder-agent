# Deep Search Agent with Linkup and `openai-agents`

## Description

This Python agent is designed to perform in-depth research on a given topic (e.g., an API, software tool, technology) using the Linkup API for web information gathering. It is built with the `openai-agents-python` SDK and can be configured to use OpenAI's LLM models or models like Anthropic's Claude via LiteLLM.

The agent receives a topic from the user, uses a specialized tool to query Linkup across various relevant information categories, and then synthesizes this information to provide a structured report.

## Features

-   **Multi-category Search**: Collects information on:
    -   Release date
    -   Reviews (GitHub, Reddit)
    -   Use cases (including verified ones and stack compatibility)
    -   Tool/API Summary (description, pros/cons, pricing)
    -   Security information (SOC 2, etc.)
-   **Linkup SDK Integration**: Uses the official Linkup Python SDK for searches.
-   **Asynchronous**: Linkup searches are performed конкурентнийly for efficiency.
-   **Configurable LLM**: Supports default OpenAI models and can be configured to use other models like Claude (Anthropic) via LiteLLM.
-   **Dependency Management**: Uses a virtual environment and a `requirements.txt` file.
-   **Centralized Configuration**: API keys and model names are managed in dedicated configuration files.

## Prerequisites

-   Python 3.8 or higher
-   `pip` (Python package manager)
-   A Linkup account and a Linkup API key.
-   An OpenAI API key (if using OpenAI models).
-   An Anthropic API key (if using Claude models via LiteLLM).

## Installation and Setup

1.  **Clone the Repository (if applicable)**
    ```bash
    # git clone <repository_url>
    # cd <project_directory_name>
    ```
    If you already have the files, skip to the next step.

2.  **Create and Activate a Virtual Environment**
    It is highly recommended to use a virtual environment to isolate project dependencies.

    *   On macOS and Linux:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
    *   On Windows (cmd.exe):
        ```bash
        python -m venv .venv
        .venv\Scripts\activate.bat
        ```
    *   On Windows (PowerShell):
        ```bash
        python -m venv .venv
        .venv\Scripts\Activate.ps1
        ```
        (If you encounter a script execution error on PowerShell, you might need to run `Set-ExecutionPolicy Unrestricted -Scope Process` and then try the activation command again.)

3.  **Install Dependencies**
    Once the virtual environment is activated, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables (`.env`)**
    Create a file named `.env` in the root of your project. Copy the contents of `.env.example` (if provided) or add the following lines and replace the values with your actual keys:

    ```env
    LINKUP_API_KEY="your_linkup_api_key_here"
    OPENAI_API_KEY="your_openai_api_key_here"
    ANTHROPIC_API_KEY="your_anthropic_api_key_here" # Required for Claude
    ```
    -   `LINKUP_API_KEY`: Your Linkup API key.
    -   `OPENAI_API_KEY`: Your OpenAI API key. Required if not using Claude or as a fallback.
    -   `ANTHROPIC_API_KEY`: Your Anthropic API key. Required for using Claude models via LiteLLM.

## Usage

To run the agent, execute the `main_agent.py` script from the root of your project (ensure your virtual environment is activated):

```bash
python main_agent.py
```

The script will then prompt you in the terminal:
`What topic do you want to research ইন depth? (e.g., OpenAI API, LangChain, FastAPI, etc.)`

Enter your desired topic and press Enter. The agent will then begin its research and synthesis process.

## File Structure

-   `main_agent.py`: Main entry point. Configures and runs the agent.
-   `agent_tools.py`: Defines `LinkupSearchTool`, the tool the agent uses for in-depth searches.
-   `linkup_service.py`: Contains the logic for interacting with the Linkup API using the Linkup SDK.
-   `config.py`: Loads and centralizes configurations like API keys and model names from environment variables.
-   `requirements.txt`: Lists the Python dependencies for the project.
-   `.env`: (To be created by the user) File for storing sensitive API keys.
-   `README.md`: This file.

## Advanced Configuration (LLM Model)

The agent is configured to use an LLM for synthesis and orchestration.

-   **OpenAI Model (Default/Fallback)**:
    If `ANTHROPIC_API_KEY` or `CLAUDE_MODEL_NAME` are not correctly configured, or if LiteLLM encounters an error, the agent will attempt to use a default OpenAI model, provided `OPENAI_API_KEY` is set in your `.env` file.

-   **Claude Model via LiteLLM**:
    To use a Claude model (e.g., Claude 3 Opus):
    1.  Ensure your `ANTHROPIC_API_KEY` is correctly set in the `.env` file.
    2.  Verify/Modify the `CLAUDE_MODEL_NAME` variable in the `config.py` file. For example:
        ```python
        CLAUDE_MODEL_NAME = "claude-3-opus-20240229" # Or the exact Claude model name you intend to use
        ```
        Ensure this model name is supported by LiteLLM and matches your Anthropic access.
    3.  Ensure `litellm` is installed (it should be if you followed the dependency installation steps).

The `main_agent.py` file contains the logic to initialize `LiteLLMModel` and pass it to the agent.

---

Feel free to contribute or report issues! 