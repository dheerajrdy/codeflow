# Memory Examples

This directory demonstrates two distinct approaches to agent memory in PicoAgents: **agent-managed memory** (agents actively control their knowledge base) and **application-managed memory** (developers control storage, framework injects context).

## Agent-Managed Memory (MemoryTool)

**File:** [`memory_tool_example.py`](memory_tool_example.py)

Agents explicitly read, write, and organize persistent knowledge through file operations. The agent decides when to check memory, what to store, and how to organize information—enabling cross-session learning where patterns discovered in one conversation can be applied in future sessions.

Memory tools utilize ideas from [Anthropic's context management work](https://www.anthropic.com/news/context-management), particularly their file-based memory system.

**Book reference:** Chapter 4, Section 4.10 "Agent-Managed Memory"

## Application-Managed Memory (ListMemory)

**File:** [`list_memory_example.py`](list_memory_example.py)

Developers call `memory.add()` to store information (user preferences, facts, conversation summaries), and the framework automatically retrieves and injects relevant context into prompts via `memory.get_context()`. The agent receives this context but does not control storage or retrieval.

**Book reference:** Chapter 4, Section 4.9 "Adding Memory"

## Running the Examples

```bash
# Navigate to examples directory
cd /path/to/designing-multiagent-systems/examples/memory

# Run agent-managed memory example
python memory_tool_example.py

# Run application-managed memory example
python list_memory_example.py
```

Both examples require `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` environment variables.

## Related Documentation

- [PicoAgents Memory Documentation](../../picoagents/docs/memory.md)
- [Book Chapter 4: Building Your First Agent](../../../../chapters/ch04-building-first-agent.qmd)
