# personal_finance_assistant/README.md

# Personal Finance Assistant

The Personal Finance Assistant is a Python application designed to help users manage their finances effectively. It integrates various tools and agents to provide a comprehensive financial analysis and response system.

## Project Structure

- **agents/**: Contains the logic for processing user queries and synthesizing responses.
  - `user_agent.py`: Handles user-facing query processing.
  - `fi_mcp_agent.py`: Performs financial analysis using MCP tools.
  - `respond_agent.py`: Synthesizes responses based on user queries and analysis results.

- **tools/**: Provides utilities for interacting with external services and performing budget analysis.
  - `wallet_tools.py`: Integrates with the Google Wallet API.
  - `mcp_client.py`: Acts as a client for the MCP protocol.
  - `budget_tools.py`: Offers utilities for budget analysis.

- **models/**: Defines data models used throughout the application.
  - `schemas.py`: Contains Pydantic data models for data validation and serialization.

- **config/**: Manages configuration settings for the application.
  - `settings.py`: Holds configuration values.

- **orchestrator.py**: Coordinates the workflow of the application.

- **main.py**: The entry point for the application.

- **enhanced_instructions.py**: Contains agent prompt templates for generating context-aware responses.

- **requirements.txt**: Lists the Python dependencies required for the project.

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

To start the application, run:

```
python main.py
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.