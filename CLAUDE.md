# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CodeFlow** is a multi-agent workflow system that automates software development tasks from Jira tickets to GitHub pull requests. The system uses specialized AI agents (Design, Coding, Review, Notes) orchestrated through an explicit workflow pattern to implement code changes, run tests, and create PRs.

This is a learning-focused project designed to explore multi-agent system patterns, particularly workflow-based orchestration, as outlined in "Designing Multi-Agent Systems" (reference materials in `docs/design/reference/mas-main/`).

**Key Architecture Decision**: This project uses Google Cloud Platform (GCP) and the Google Agent Development Kit, NOT the PicoAgents framework shown in reference materials.

## Project Structure

```
/
├── src/                      # Main application code
│   ├── agents/              # Agent implementations
│   │   ├── design_agent.py
│   │   ├── coding_agent.py
│   │   ├── review_agent.py
│   │   └── notes_agent.py
│   ├── orchestration/       # Workflow engine
│   │   ├── workflow_engine.py
│   │   └── steps.py
│   ├── integrations/        # External service integrations
│   │   ├── jira_client.py
│   │   ├── github_client.py
│   │   └── vcs_utils.py
│   ├── models/              # Model client abstractions
│   │   └── model_client.py
│   └── cli/                 # CLI interface
│       └── run_workflow.py
├── tests/                   # Test suite
├── docs/                    # Documentation
│   └── design/             # Design documents
│       ├── design.md       # Complete design & 6-day plan
│       └── reference/      # PicoAgents reference (DO NOT import)
├── runs/                    # Workflow run logs & metadata
└── config.yaml             # Configuration file
```

## Core Concepts

### Multi-Agent Pattern

The system uses **workflow-based orchestration** (not autonomous group chat):
- **Design Agent**: Analyzes Jira ticket, proposes implementation approach, identifies target files
- **Coding Agent**: Generates code changes as patches/diffs based on design plan
- **Review Agent**: Evaluates diff against acceptance criteria, approves or requests changes
- **Notes/Metadata Agent**: Summarizes run, captures lessons learned, suggests improvements

### Workflow Pattern

Sequential pipeline with conditional branches:
```
FetchTicket → AnalyzeRepo → Design → Code → Test → Review → PR → Notes
```

Retry logic:
- If tests fail → one retry to Coding Agent with test output
- If Review rejects → one retry cycle, then abort
- All failures are logged for learning

### Model Abstraction

`ModelClient` interface keeps agents model-agnostic. Initial implementation uses Google's models via GCP Agent Development Kit.

## Development Commands

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (once requirements.txt exists)
pip install -r requirements.txt

# Set up credentials
export JIRA_API_TOKEN="your-jira-token"
export GITHUB_TOKEN="your-github-token"
export GOOGLE_CLOUD_PROJECT="your-gcp-project"
# Additional GCP credentials as needed
```

### Running Workflows

```bash
# Run full workflow for a Jira ticket
python -m src.cli.run_workflow --ticket JIRA-123

# Dry run (no git operations)
python -m src.cli.run_workflow --ticket JIRA-123 --dry-run

# Show recent runs
python -m src.cli.run_workflow --list-runs
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_agents.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking (if using mypy)
mypy src/ --ignore-missing-imports
```

## Configuration

Edit `config.yaml` to configure:
- **Jira**: base URL, project key, API token env var
- **GitHub**: org/repo, token env var
- **Test command**: e.g., `pytest`, `npm test`
- **Model config**: provider, model name, temperature, max tokens

Example:
```yaml
jira:
  base_url: "https://your-company.atlassian.net"
  project_key: "PROJ"
  api_token_env: "JIRA_API_TOKEN"

github:
  org: "your-org"
  repo: "your-repo"
  token_env: "GITHUB_TOKEN"

test:
  command: "pytest"

model:
  provider: "google"  # Using GCP Agent Development Kit
  model_name: "gemini-pro"  # Or appropriate Google model
  temperature: 0.7
  max_tokens: 2048
```

## Agent Design Patterns

### Design Agent
- **Input**: Jira ticket (title, description, acceptance criteria), basic repo info
- **Output**: Problem understanding, proposed approach, target files, step-by-step plan
- **Key Concern**: Avoid over-scoping changes; reference acceptance criteria explicitly

### Coding Agent
- **Input**: Ticket, Design Agent output, code snippets from candidate files
- **Output**: Code changes as patches/diffs, explanations of non-obvious changes
- **Key Concern**: Generate minimal necessary changes; keep code syntactically correct

### Review Agent
- **Input**: Ticket, design output, diff, test results
- **Output**: Decision (approve/request changes), review comments, suggestions
- **Key Concern**: Align review with acceptance criteria

### Notes/Metadata Agent
- **Input**: Full workflow context (steps, outputs, errors, test results, PR link)
- **Output**: Human-readable summary, lessons learned about repo/workflow, tags/labels
- **Storage**: Logs stored in `runs/` directory (JSONL or SQLite)

## Workflow Step Definitions

Each workflow step is responsible for:
1. Taking shared `WorkflowContext` as input
2. Performing its specific operation
3. Updating context with results
4. Handling errors gracefully
5. Logging progress

Example step structure:
```python
class DesignStep:
    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        # Read ticket from context
        # Call Design Agent
        # Update context.design_output
        # Return updated context
```

## Git & GitHub Operations

### Safety Protocol
- **NEVER** push directly to main/master
- **ALWAYS** create feature branches with conventional naming (e.g., `feature/JIRA-123-description`)
- **CONFIRM** before destructive operations unless `--no-confirm` flag is used
- Use standard commit message format with co-authoring

### Branch Naming Convention
```
feature/JIRA-123-short-description
bugfix/JIRA-456-issue-description
```

### PR Creation
- Title: From ticket summary or design output
- Body: Auto-generated from Design and Coding Agent outputs, includes:
  - Link to Jira ticket
  - Summary of changes
  - Test results
  - Review notes

## Run Metadata & Learning

Each workflow run stores:
- `run_id`, `ticket_id`, timestamps
- Step results (design plan, diff, test output, review decision)
- PR URL (if created)
- Notes Agent summary and lessons learned

Access via:
```bash
python -m src.cli.run_workflow --list-runs
python -m src.cli.run_workflow --show-run <run_id>
```

Use this data to:
- Refine agent prompts
- Adjust workflow steps
- Identify patterns in repo/ticket types
- Improve retry logic

## Important Design Principles

### From "Designing Multi-Agent Systems" (Applied)
- ✅ **Role-specialized agents**: Each agent has clear responsibilities
- ✅ **Explicit orchestration**: Workflow engine controls execution order
- ✅ **Model abstraction**: ModelClient keeps agents provider-agnostic
- ✅ **Evaluation-first**: Track runs, metrics, iterate on prompts
- ✅ **Observability & control**: Clear logs, confirmation gates, dry-run mode

### Intentionally Omitted (for v1)
- ❌ Autonomous group chat orchestration
- ❌ Heavy long-term memory / RAG infrastructure
- ❌ DAG-based parallel workflow execution
- ❌ Computer-use / UI-control agents
- ❌ LLM-as-judge evaluation frameworks
- ❌ Multi-user / product-grade UX

### Simplicity Guidelines
- Keep workflows sequential with simple conditionals
- One retry loop per failure type, then abort
- Start with text-based repo summaries (no vector DB initially)
- CLI-first, web UI later if needed
- Focus on learning and iteration, not production scale

## Common Tasks

### Adding a New Agent
1. Create agent class in `src/agents/`
2. Define input/output schema
3. Implement prompt template
4. Wire into workflow in `src/orchestration/workflow_engine.py`
5. Add tests in `tests/`

### Modifying Workflow Steps
1. Update step logic in `src/orchestration/steps.py`
2. Adjust conditionals in `workflow_engine.py`
3. Update config if new parameters needed
4. Test with `--dry-run` first

### Debugging Failed Runs
1. Check run logs in `runs/` directory
2. Review Notes Agent output for insights
3. Use `--dry-run` to test changes without side effects
4. Verify Jira/GitHub connectivity separately

### Iterating on Prompts
1. Locate prompt template in agent file
2. Modify prompt text
3. Test with known ticket (use eval set if available)
4. Compare runs using Notes Agent summaries
5. Commit prompt changes with run metrics

## Technology Stack

- **Language**: Python 3.10+
- **Agent Framework**: Google Cloud Agent Development Kit (NOT PicoAgents)
- **LLM Provider**: Google Cloud (Gemini models)
- **VCS**: Git via GitPython or subprocess
- **Integrations**:
  - Jira: REST API via `requests` or `jira` library
  - GitHub: REST API via `PyGithub` or `requests`
- **Testing**: pytest
- **Config**: YAML (via `pyyaml`)
- **Storage**: Local files (JSONL) or SQLite for run metadata

## Reference Materials

The `docs/design/reference/mas-main/` directory contains the PicoAgents framework as a **reference implementation only**.

**DO NOT**:
- Import PicoAgents code into this project
- Copy PicoAgents code verbatim
- Use PicoAgents as a dependency

**DO**:
- Study patterns and architecture
- Understand agent abstractions (tools, memory, middleware)
- Learn workflow orchestration approaches
- Reference for multi-agent design principles
- Adapt concepts to Google Cloud Agent Development Kit

## Evaluation & Iteration

### Evaluation Set
Create 3-5 "training" tickets (real or synthetic) with known good solutions:
- Small but representative of typical work
- Cover different change types (new feature, bug fix, refactor)
- Store in `tests/fixtures/eval_tickets/`

### Running Evaluation
```bash
# Once implemented
python -m src.cli.eval --tickets JIRA-1,JIRA-2,JIRA-3
```

### Metrics to Track
- End-to-end success (PR created, tests pass)
- Review pass/fail (automated)
- Manual quality rating (1-5)
- Agent-specific metrics (design quality, code correctness)

### Iteration Cycle
1. Run eval set
2. Review Notes Agent output
3. Identify failure patterns
4. Adjust prompts/workflow/retry logic
5. Re-run eval set
6. Document improvements

## Development Roadmap (6-Day Plan)

Detailed plan in `docs/design/design.md`:
1. **Day 1**: Scaffolding & workflow runner stub
2. **Day 2**: Model & agent interfaces (Design + Review agents)
3. **Day 3**: Coding Agent + Jira/GitHub integration (end-to-end happy path)
4. **Day 4**: Notes Agent + observability
5. **Day 5**: Guardrails, error handling, CLI UX
6. **Day 6**: Evaluation harness, examples, documentation

## Questions & Feedback

For design decisions or architectural questions, refer to:
- `docs/design/design.md` - Complete design document with 6-day plan
- "Designing Multi-Agent Systems" book concepts (summarized in design.md)
- Reference PicoAgents implementation patterns

When implementing new features, prefer:
- Clear, explicit workflows over complex abstractions
- Simple sequential steps over parallelism (initially)
- Minimal viable changes over over-engineering
- Learning and iteration over production polish
- always refer and use design.md to make sure we are on right track and building what is required.