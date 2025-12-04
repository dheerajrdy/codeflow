# Minimal Agent Web Application

A complete, minimal example demonstrating the three fundamental layers of any agent web application:

1. **Agent Execution** - PicoAgents running the agent logic
2. **Communication Bridge** - FastAPI + Server-Sent Events for real-time streaming
3. **User Interface** - Vanilla JavaScript consuming the event stream

**Total code:** ~200 lines (100 backend, 100 frontend)

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key

### 1. Install Dependencies & Set API Key

```bash
# Install dependencies
pip install picoagents fastapi "uvicorn[standard]"

# Set your API key
export OPENAI_API_KEY=your-key-here
```

### 2. Start the Backend

**Option A: Run directly (simplest)**
```bash
cd examples/app/backend
python app.py
```

**Option B: Run with uvicorn (more control)**
```bash
cd examples/app/backend
uvicorn app:app --reload
```

The server starts on `http://localhost:8000` and automatically serves the frontend.

### 3. Open Your Browser

Simply navigate to `http://localhost:8000` - the frontend is served automatically!

### 4. Try It Out

Ask the weather assistant about weather in different cities:
- "What's the weather in Paris?"
- "How's the weather in Tokyo?"
- "Tell me about New York weather"

Watch the agent stream its response in real-time, including:
- Token-by-token text streaming
- Tool execution indicators
- Final formatted response

## Architecture

### Layer 1: Agent Execution (`backend/app.py` lines 18-35)

```python
# Define a simple tool
def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 72°F"

# Create an agent
weather_agent = Agent(
    name="weather_assistant",
    model_client=OpenAIChatCompletionClient(model="gpt-4.1-mini"),
    instructions="Help users check weather using the get_weather tool",
    tools=[get_weather],
)
```

The agent execution layer handles all the AI logic - reasoning, tool calling, and response generation. This is completely decoupled from the UI.

### Layer 2: Communication Bridge (`backend/app.py` lines 55-91)

```python
async def stream_agent_events(message: str):
    """Stream agent events as Server-Sent Events."""
    async for event in weather_agent.run_stream(message, stream_tokens=True):
        yield f"data: {event.model_dump_json()}\n\n"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        stream_agent_events(request.message),
        media_type="text/event-stream",
    )
```

The communication bridge:
- Receives user input via REST endpoint
- Streams agent execution events in real-time
- Uses Server-Sent Events (SSE) protocol
- Bridges between agent execution and UI

**Why SSE?** Simple, built into browsers, perfect for server-to-client streaming.

### Layer 3: User Interface (`frontend/index.html`)

```javascript
// Consume the SSE stream
const response = await fetch('http://localhost:8000/chat/stream', {
    method: 'POST',
    body: JSON.stringify({ message }),
});

const reader = response.body.getReader();
// Read and process events as they arrive...
```

The UI:
- Sends user messages to the backend
- Consumes the SSE stream
- Updates the interface in real-time as events arrive
- No framework needed - just vanilla JavaScript

## Key Concepts Demonstrated

### 1. **Event-Driven Architecture**
The agent emits events (thinking, tool calling, responding), the backend forwards them, and the UI reacts to them.

### 2. **Streaming for Real-Time Feedback**
Users see the agent working in real-time rather than waiting for a final response.

### 3. **Separation of Concerns**
- Agent doesn't know about HTTP or browsers
- Backend doesn't know about DOM or UI
- Frontend doesn't know about agent implementation
- Each layer can be swapped independently

### 4. **Production-Ready Pattern**
This same architecture scales to complex applications:
- Add more agents → Layer 1
- Add authentication, caching → Layer 2
- Build sophisticated UI → Layer 3

## Extending This Example

**Add more agents:**
```python
math_agent = Agent(name="math", tools=[calculator])
research_agent = Agent(name="researcher", tools=[web_search])
```

**Add orchestration:**
```python
from picoagents.orchestration import RoundRobinOrchestrator

orchestrator = RoundRobinOrchestrator(
    agents=[weather_agent, math_agent],
    termination=MaxMessageTermination(max_messages=10)
)
```

**Improve the UI:**
- Add React, Vue, or your favorite framework
- Add message history persistence
- Add agent selection UI
- Add file upload for document agents

**Production deployment:**
- Add authentication middleware
- Add rate limiting
- Add database for conversation history
- Deploy with Docker/Kubernetes

## Why This Matters

This minimal example demonstrates that building agent UIs isn't complicated - it's about understanding the three layers and connecting them properly. Once you understand this pattern, you can build UIs for any agent system, using any technology stack.

The same pattern works whether you're using:
- **Different agents:** AutoGen, LangChain, custom implementations
- **Different backends:** Express.js, Flask, Django
- **Different frontends:** React, Vue, Streamlit, CLI

The three-layer architecture is universal.
