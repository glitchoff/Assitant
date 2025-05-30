import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LangChain components
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Initialize FastAPI
app = FastAPI(
    title="Chatbot with Tool Calling",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates directory
templates = Jinja2Templates(directory="templates")


# Define tools for the agent
@tool
def get_weather(city: str) -> str:
    """Get the current weather in a given city."""
    # In a real application, you would call a weather API here
    return f"The weather in {city} is sunny and 25°C"


@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # In a real application, you would call a search API here
    return f"Search results for '{query}': This is a simulated search result."


# Initialize the language model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Set up tools
tools = [get_weather, search_web]

# Create prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Use the available tools when appropriate."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Create the agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Store chat histories (in-memory for this example)
chat_histories: Dict[str, BaseChatMessageHistory] = {}


def get_chat_history(session_id: str) -> BaseChatMessageHistory:
    """Get or create chat history for a session."""
    if session_id not in chat_histories:
        chat_histories[session_id] = ChatMessageHistory()
    return chat_histories[session_id]


# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str


# API endpoint for chat
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Get or create chat history for this session
        chat_history = get_chat_history(request.session_id)
        
        # Add user message to history
        chat_history.add_user_message(request.query)
        
        # Run the agent
        response = await agent_executor.ainvoke(
            {"input": request.query, "chat_history": chat_history.messages}
        )
        
        # Add AI response to history
        chat_history.add_ai_message(response["output"])
        
        return ChatResponse(
            response=response["output"],
            session_id=request.session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to clear chat history
@app.post("/clear_history/{session_id}")
async def clear_history(session_id: str):
    if session_id in chat_histories:
        chat_histories[session_id].clear()
    return {"status": "History cleared"}


# Root endpoint - Serve the chat interface
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
