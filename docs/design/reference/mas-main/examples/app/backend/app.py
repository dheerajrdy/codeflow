"""
Minimal agent web application backend.

A FastAPI server that demonstrates the three layers of agent applications:
1. Agent Execution (PicoAgents)
2. Communication Bridge (FastAPI + SSE)
3. User Interface (served static HTML)

Prerequisites:
    pip install picoagents fastapi "uvicorn[standard]"

Run:
    cd examples/app/backend
    export OPENAI_API_KEY=your-key-here
    python app.py

Then open: http://localhost:8000
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from picoagents import Agent, CancellationToken, OpenAIChatCompletionClient


# ============================================================================
# Layer 1: Agent Execution
# ============================================================================

def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Weather in {location}: Sunny, 72°F"


# Create our agent
weather_agent = Agent(
    name="weather_assistant",
    description="A weather assistant that provides weather information",
    model_client=OpenAIChatCompletionClient(model="gpt-4.1-mini"),
    instructions="Help users check weather using the get_weather tool",
    tools=[get_weather],
)


# ============================================================================
# Layer 2: Communication Bridge (FastAPI + SSE)
# ============================================================================

app = FastAPI(title="Minimal Agent Web App")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """User message request."""

    message: str


async def stream_agent_events(
    message: str, cancellation_token: CancellationToken
) -> AsyncGenerator[str, None]:
    """
    Stream agent execution events as Server-Sent Events with cancellation support.

    This is the key bridge between agent execution and the UI.
    It converts agent events into SSE format that browsers can consume.
    The cancellation_token allows graceful interruption of long-running tasks.
    """
    try:
        # Stream events from the agent, passing the cancellation token
        async for event in weather_agent.run_stream(
            message, stream_tokens=True, cancellation_token=cancellation_token
        ):
            # Format as Server-Sent Event
            # The "data: " prefix is required by the SSE protocol
            yield f"data: {event.model_dump_json()}\n\n"

    except (GeneratorExit, asyncio.CancelledError):
        # Client disconnected (e.g., clicked Stop button)
        # Trigger cancellation to stop agent execution and save resources
        cancellation_token.cancel()
        raise


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Handle chat requests with streaming responses and cancellation support.

    This endpoint demonstrates the communication bridge pattern:
    - Receives user input
    - Streams agent execution in real-time
    - Returns events as Server-Sent Events
    - Supports graceful cancellation when client disconnects
    """
    # Create a cancellation token for this request
    # If the client disconnects, we'll use this to stop the agent
    cancellation_token = CancellationToken()

    return StreamingResponse(
        stream_agent_events(request.message, cancellation_token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "agent": weather_agent.name}


# ============================================================================
# Layer 3: Serve Frontend
# ============================================================================

# Mount the frontend directory to serve static files
# In production, you'd use a CDN or separate static file server
import os
from pathlib import Path

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Minimal Agent Web App")
    print(f"📍 Server: http://localhost:8000")
    print(f"🤖 Agent: {weather_agent.name}")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
