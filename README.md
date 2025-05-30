# Chatbot with Tool Calling

A Python-based chatbot that uses LangChain and Google's Gemini model to provide intelligent responses with tool calling capabilities. The chatbot is built with FastAPI and supports conversation history.

## Features

- **Tool Calling**: The bot can use predefined tools like weather lookup and web search
- **Conversation History**: Maintains conversation context within a session
- **REST API**: Provides a simple HTTP API for integration
- **Environment Configuration**: Uses `.env` for API keys and configuration

## Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Google Gemini API key (set in `.env` file)

## Installation

1. Clone the repository
2. Install dependencies using `uv`:

```bash
uv pip install -e .
```

3. Create a `.env` file in the project root with your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

## Running the Application

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /`: Check if the API is running
- `POST /chat`: Send a message to the chatbot
  - Request body: `{"message": "Your message here", "session_id": "optional_session_id"}`
  - Response: `{"response": "Bot's response", "session_id": "session_id"}`
- `POST /clear_history/{session_id}`: Clear chat history for a session

## Example Usage

### Using cURL

```bash
# Send a message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What\'s the weather in Paris?"}'

# Clear chat history
curl -X POST http://localhost:8000/clear_history/default
```

### Using Python

```python
import requests

# Send a message
response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "What's the weather in Tokyo?"}
)
print(response.json())

# Clear history
requests.post("http://localhost:8000/clear_history/default")
```

## Available Tools

1. `get_weather(city: str)`: Get the current weather for a city
2. `search_web(query: str)`: Search the web for information

## Development

To add new tools, simply create a new function with the `@tool` decorator and add it to the `tools` list in `main.py`.

## License

MIT