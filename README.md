# CodeFlow

Multi-agent workflow system for automated code changes from Jira tickets to GitHub pull requests.

## Overview

CodeFlow automates the software development workflow by using specialized AI agents to:
- Analyze Jira tickets and propose implementation approaches
- Generate code changes based on design plans
- Run tests and perform automated code reviews
- Create pull requests and capture learnings

## Quick Start

### Setup

```bash
# Create and activate uv environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the project
uv pip install -e ".[dev]"
```

### Run a Workflow

```bash
# Run workflow in stub mode (no AI)
python -m src.cli --ticket JIRA-123 --dry-run

# Run with real AI agents (requires GOOGLE_API_KEY)
export GOOGLE_API_KEY="your-api-key-here"
python examples/day2_demo.py

# Day 3 demo with Coding Agent + integrations (safe dry-run by default)
export GOOGLE_API_KEY="your-api-key-here"
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="token"
export GITHUB_REPO="owner/repo"
export GITHUB_TOKEN="ghp_xxx"
python examples/day3_demo.py

# Day 5 guardrails/config examples
# Use config file (defaults to ./config.yaml if present)
python -m src.cli --ticket JIRA-123 --config ./config.yaml
# Auto-confirm git/PR actions (skip interactive prompt)
python -m src.cli --ticket JIRA-123 --yes

# Day 6 evaluation harness (stub-friendly; saves report to runs/)
export EVAL_TICKETS="EVAL-1,EVAL-2"
python examples/day6_eval.py

# List or inspect saved runs (after any workflow run)
python -m src.cli --list-runs
python -m src.cli --show-run <run_id>
```

### Run Tests

```bash
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Project Status

**Current Phase: Day 6 (Evaluation harness & examples)**

- [x] Project scaffolding and structure
- [x] Workflow engine with sequential step execution
- [x] CLI entrypoint
- [x] Stubbed workflow steps
- [x] Basic tests
- [x] **Model & agent interfaces (Day 2)**
  - [x] ModelClient abstraction
  - [x] Google Gemini client implementation
  - [x] Design Agent with prompt templates
  - [x] Review Agent with prompt templates
- [x] **Day 3 additions**
  - [x] Coding Agent that produces real patches/diffs
  - [x] Jira client for ticket fetching (stub-friendly)
  - [x] GitHub client for branch/PR creation (dry-run friendly)
  - [x] CLI/demo wiring for end-to-end flow
- [x] **Day 4 additions**
  - [x] Notes/Metadata Agent
  - [x] Run persistence to `runs/` with logs
  - [x] CLI commands to list/show past runs
- [x] **Day 5 additions**
  - [x] Guardrails for git/PR actions (prompts with `--yes` override)
  - [x] Retry loop for Coding/Test/Review (configurable `max_retries`)
  - [x] Config loading from `config.yaml`
  - [x] Better CLI UX for run listing/showing
- [x] **Day 6 additions**
  - [x] Evaluation harness to run multiple tickets and capture metrics
  - [x] Day 6 evaluation demo script

## Architecture

CodeFlow uses a workflow-based orchestration pattern with specialized agents:

- **Design Agent**: Analyzes tickets and proposes implementation approaches
- **Coding Agent**: Generates code changes as patches/diffs
- **Review Agent**: Evaluates changes against acceptance criteria
- **Notes Agent**: Captures learnings and metadata

See [CLAUDE.md](CLAUDE.md) for detailed architecture and development guidance.

## Development

### Project Structure

```
codeflow/
├── src/
│   ├── agents/          # Agent implementations
│   ├── orchestration/   # Workflow engine & steps
│   ├── integrations/    # Jira, GitHub clients
│   ├── models/          # Model client abstractions
│   └── cli/             # CLI interface
├── tests/               # Test suite
├── docs/                # Documentation
└── runs/                # Workflow run logs
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_workflow.py -v

# With coverage
pytest --cov=src
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

## Configuration

Configuration is managed through `config.yaml` (to be implemented in Day 5).

Example structure:
```yaml
jira:
  base_url: "https://your-company.atlassian.net"
  project_key: "PROJ"

github:
  org: "your-org"
  repo: "your-repo"

test:
  command: "pytest"

model:
  provider: "google"
  model_name: "gemini-pro"
```

Environment variables supported (override config.yaml):
- `GOOGLE_API_KEY`, `GOOGLE_MODEL`
- `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`
- `GITHUB_REPO`, `GITHUB_TOKEN`, `GITHUB_DEFAULT_BRANCH`
- `REPO_PATH`, `TEST_COMMAND`
- `CODEFLOW_CONFIG` (custom config path), `CODEFLOW_AUTO_CONFIRM` (`true` to skip prompts)

## Documentation

- [CLAUDE.md](CLAUDE.md) - Guidance for Claude Code when working on this project
- [docs/design/design.md](docs/design/design.md) - Complete design document with 6-day plan
- [docs/design/reference/](docs/design/reference/) - Reference implementations (PicoAgents)

## License

This is a learning project following the design principles from "Designing Multi-Agent Systems" by Victor Dibia.

## Implementation Notes

This project is being built over 6 days following a structured plan:

1. **Day 1 ✓**: Scaffolding & workflow runner stub
2. **Day 2**: Model & agent interfaces
3. **Day 3**: Coding Agent + Jira/GitHub integration
4. **Day 4**: Notes Agent + observability
5. **Day 5**: Guardrails & UX polish
6. **Day 6**: Evaluation harness & examples

See [docs/design/design.md](docs/design/design.md) for the complete implementation plan.
