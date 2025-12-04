# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the official code repository for "Designing Multi-Agent Systems: Principles, Patterns, and Implementation for AI Agents" by Victor Dibia. It contains **PicoAgents**—a full-featured educational multi-agent framework built from scratch to teach how multi-agent systems work, plus 50+ runnable examples organized by book chapter.

The repository is organized into two main sections:
- **picoagents/** - The core framework implementation
- **examples/** - Working examples demonstrating framework usage

## Environment Setup

### Using uv (Recommended for Development)

```bash
# Create and activate a uv environment at repository root
# (this allows examples/ to import picoagents correctly)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the framework from the picoagents/ subdirectory
uv pip install -e "./picoagents[examples]"

# Note: anthropic library is required even for OpenAI-only usage due to imports
# It's included automatically when using [examples] or [all]
# Or install with other optional features:
uv pip install -e "./picoagents[web]"           # Web UI and API server
uv pip install -e "./picoagents[computer-use]"  # Browser automation
uv pip install -e "./picoagents[all]"           # Everything

# Set up API key
export OPENAI_API_KEY="your-api-key-here"
```

### Using pip

```bash
# Create venv at repository root (allows examples/ to import picoagents)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e "./picoagents[examples]"
export OPENAI_API_KEY="your-api-key-here"
```

### Optional Features
- `[web]` - FastAPI server and Web UI
- `[computer-use]` - Playwright for browser automation agents
- `[rag]` - ChromaDB and embeddings for RAG
- `[research]` - Web scraping and research tools
- `[mcp]` - Model Context Protocol support
- `[anthropic]` - Anthropic Claude support
- `[examples]` - Dependencies for running examples
- `[dev]` - Development tools (pytest, mypy, black, etc.)
- `[all]` - All optional features

## Running Examples

Examples are located at the repository root for easy access:

```bash
# From repository root (not from picoagents/)

# Basic agent with tools (Chapter 4)
python examples/agents/basic-agent.py

# Browser automation agent (Chapter 5)
python examples/agents/computer_use.py

# Orchestration patterns (Chapter 7)
python examples/orchestration/round-robin.py
python examples/orchestration/ai-driven.py
python examples/orchestration/plan-based.py

# Production workflow case study (Chapter 16)
python examples/workflows/yc_analysis/workflow.py
```

## Testing and Development

All development commands should be run from the `picoagents/` directory:

```bash
cd picoagents

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/picoagents --cov-report=term-missing

# Type checking
mypy src/ --show-error-codes --ignore-missing-imports
pyright src/

# Code formatting
black src/ examples/ tests/
isort src/ examples/ tests/

# Linting
flake8 src/ examples/ tests/

# Using poethepoet task runner (if installed with [dev])
poe test          # Run tests
poe test-cov      # Tests with coverage
poe mypy          # Type check with mypy
poe pyright       # Type check with pyright
poe check         # Run all checks (mypy, pyright, lint, test)
```

## Web UI

Launch the interactive web interface with auto-discovery:

```bash
# From repository root
picoagents ui

# Or specify a directory to discover agents/orchestrators/workflows
picoagents ui --dir ./examples

# Custom port
picoagents ui --port 8080
```

The Web UI provides:
- Streaming chat interface
- Real-time debug events
- Session management
- Auto-discovery of agents, orchestrators, and workflows in specified directory

## Architecture

### Core Components (picoagents/src/picoagents/)

**agents/** - Agent implementations
- `_agent.py` - Complete agent with reasoning loop, tool calling, memory, middleware, streaming
- `_base.py` - Base agent interface
- `_computer_use/` - Browser automation agents with Playwright integration

**workflow/** - Type-safe DAG-based workflow engine
- `core/` - Workflow execution engine with streaming observability
- `steps/` - Reusable workflow steps (AgentStep, LLMStep, ToolStep, etc.)

**orchestration/** - Autonomous multi-agent coordination patterns
- `_round_robin.py` - Sequential turn-taking
- `_ai.py` - LLM-driven speaker selection (GroupChat pattern)
- `_plan.py` - Plan-based orchestration (Magentic One pattern)
- `_base.py` - Universal orchestration loop and base interface

**tools/** - Tool system and 15+ built-in tools
- `_base.py` - Base tool interface
- `_decorator.py` - Tool decorator for function-to-tool conversion
- `_core_tools.py` - Core tools (think, ask_question, send_message)
- `_coding_tools.py` - Code execution and workspace management
- `_research_tools.py` - Web search, scraping, content extraction
- `_mcp/` - Model Context Protocol integration

**llm/** - Model client implementations
- `_openai.py` - OpenAI and OpenAI-compatible clients (works with GitHub Models, Ollama, etc.)
- `_azure_openai.py` - Azure OpenAI client
- `_anthropic.py` - Anthropic Claude client
- `_base.py` - Base model client interface

**eval/** - Evaluation framework
- `judges/` - LLM-as-judge, reference-based validators
- `_runner.py` - Test execution and metrics collection

**memory/** - Memory implementations
- `_base.py` - Base memory interface
- `_chromadb.py` - ChromaDB-based vector memory

**termination/** - 9+ termination conditions for orchestration
- `_max_message.py` - Max message count
- `_timeout.py` - Time-based termination
- `_text_mention.py` - Keyword/phrase detection
- `_handoff.py` - Agent handoff termination
- Supports composition with `|` (OR) and `&` (AND)

**_middleware.py** - Extensible middleware system for agents

**context.py** - AgentContext for managing conversation state and memory

**messages.py** - Message types (UserMessage, AssistantMessage, ToolMessage, etc.)

**types.py** - Event types for streaming (ModelCallEvent, ToolCallEvent, etc.)

**_component_config.py** - Component serialization and configuration system

**_otel.py** - OpenTelemetry integration for observability

### Key Patterns

**Agent Execution Flow**:
1. Agent receives task (string, UserMessage, or Message list)
2. Enters reasoning loop (up to max_iterations)
3. Calls LLM with context + tools
4. If tool calls: executes tools, adds results to context
5. If no tool calls or summarize_tool_result=True: returns response
6. Streams events (ModelCallEvent, ToolCallEvent, etc.) throughout

**Orchestration Flow**:
1. Initialize with agents list and termination condition
2. Universal loop: select_next_agent() → agent.run() → check termination
3. Shared message history maintained across all agents
4. Termination checked after each agent turn
5. Streams OrchestrationEvent objects for observability

**Workflow Execution**:
1. Build DAG with steps and edges
2. Validate graph (no cycles, single start, valid end states)
3. Execute steps respecting dependencies
4. Pass typed state between steps
5. Support parallel execution of independent steps

### Model Client Setup

PicoAgents uses a unified model client interface. Examples show how to use different providers:

```python
# OpenAI (default)
from picoagents.llm import OpenAIChatCompletionClient
client = OpenAIChatCompletionClient(model="gpt-4.1-mini")

# Anthropic
from picoagents.llm import AnthropicChatCompletionClient
client = AnthropicChatCompletionClient(model="claude-3-5-sonnet-20241022")

# Azure OpenAI
from picoagents.llm import AzureOpenAIChatCompletionClient
client = AzureOpenAIChatCompletionClient(
    endpoint="https://your-resource.openai.azure.com",
    api_key="your-key",
    deployment_name="your-deployment"
)

# GitHub Models (free tier, OpenAI-compatible)
client = OpenAIChatCompletionClient(
    model="openai/gpt-4.1-mini",
    api_key=os.getenv("GITHUB_TOKEN"),
    base_url="https://models.github.ai/inference"
)

# Local LLM (Ollama, LM Studio, etc.)
client = OpenAIChatCompletionClient(
    model="llama3.2",
    base_url="http://localhost:11434/v1"
)
```

See `examples/agents/agent_*.py` files for working examples with each provider.

## Important Development Notes

1. **Python Version**: Requires Python 3.10+
2. **Async/Await**: Most agent methods are async and must be awaited or run with `asyncio.run()`
3. **Type Safety**: Framework uses strict typing with mypy and pyright in strict mode
4. **Educational Focus**: Code prioritizes clarity and pedagogical value over performance optimization
5. **Streaming First**: All agent and orchestrator interactions support streaming with detailed events
6. **Component System**: Agents, orchestrators, workflows, and tools can be serialized/deserialized via the Component system

## Common Tasks

**Run a single test file**:
```bash
cd picoagents
pytest tests/test_agents.py -v
```

**Run specific test**:
```bash
cd picoagents
pytest tests/test_agents.py::test_agent_basic -v
```

**Install Playwright browsers** (for computer-use agents):
```bash
playwright install chromium
```

**Check what's discoverable by Web UI**:
```bash
# The Web UI auto-discovers agents, orchestrators, and workflows
# that are instantiated at module level in Python files
picoagents ui --dir ./examples
```

## Example Structure

Examples are organized by book chapter:
- `examples/agents/` - Ch 4-5: Basic agents, tools, memory, computer use
- `examples/workflows/` - Ch 6: Sequential, parallel, production workflows
- `examples/orchestration/` - Ch 7: Round-robin, AI-driven, plan-based
- `examples/evaluation/` - Ch 10: Agent evaluation patterns
- `examples/app/` - Ch 8: Minimal FastAPI + SSE server example
- `examples/notebooks/` - Jupyter notebook versions with Colab support

Many examples support both CLI and Web UI modes via `--web` flag.

## API Keys

The framework requires API keys for LLM providers:
- OpenAI: `export OPENAI_API_KEY="sk-..."`
- Anthropic: `export ANTHROPIC_API_KEY="sk-..."`
- Azure: Set via client initialization (endpoint, api_key, deployment_name)
- GitHub Models: `export GITHUB_TOKEN="ghp_..."`

## Additional Resources

- Main repository: https://github.com/victordibia/designing-multiagent-systems
- Book: https://buy.multiagentbook.com
- Issues: https://github.com/victordibia/designing-multiagent-systems/issues
