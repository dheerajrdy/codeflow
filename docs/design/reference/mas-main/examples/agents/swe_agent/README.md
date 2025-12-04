# Software Engineering Agent

Autonomous coding agent demonstrating the **agent + tools + memory** pattern used by GitHub Copilot, Cursor, and Claude Code.

## Core Concepts

**Agent capabilities emerge from three components:**
• **Tools**: File operations, code execution, memory, metacognition
• **Prompts**: Structured workflow encoding best practices
• **Memory**: Persistent knowledge across sessions

## Engineering Patterns

**Five-phase workflow**: Memory check → Planning → Execution → Learning → Completion
**Surgical edits**: `str_replace` mode for precise changes
**Markdown tracking**: Checkboxes in `/memories/current_task.md`
**Explicit evaluation**: `TaskStatusTool` prevents premature termination

## Quick Start

```bash
# Set credentials
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-key"

# Run example
cd examples/agents/swe_agent
python agent.py
```

## What It Does

Runs three tasks showing memory usage:

**Task 1**: Create calculator module + tests
**Task 2**: Add power function (reuses testing patterns from Task 1)
**Task 3**: Add documentation (applies learned conventions)

## Agent Architecture

**File Tools**: `read_file`, `write_file` (3 modes), `list_directory`, `grep_search`
**Execution**: `python_repl`, `bash_execute`
**Memory**: `view`, `create`, `search`, `append`, `str_replace`
**Metacognition**: `ThinkTool`, `TaskStatusTool`

**Memory structure**:
```
agent_memory/
├── patterns/           # Reusable solutions
├── decisions/          # Dated decision logs
├── current_task.md     # Active plan with checkboxes
└── project_context.md  # High-level understanding
```

## Configuration

**Iteration limits** (in `Agent`):
- Simple scripts: 10-20
- Multi-file projects: 30-50 (default)
- Complex refactoring: 50-100

**Bash timeout** (in `create_coding_tools`):
- 30s: Quick tests
- 60s: Test suites (default)
- 120s+: Large builds

## Files

- `agent.py` - Main agent setup and example tasks
- `scratch/agent_workspace/` - Generated code (isolated)
- `scratch/agent_memory/` - Persistent memory

## Key Insights

**Tools are prerequisites, not guarantees.** Quality depends on LLM capabilities, prompt guidance, and feedback from execution.

**Prompts are software.** They encode workflows, best practices, and completion criteria. Iterate and test them.

**Memory enables learning.** Patterns accumulate, mistakes are recorded, decisions are justified. Agent improves over time.

**Completion needs explicit criteria.** Clear requirements + `TaskStatusTool` + tests = reliable task completion.
