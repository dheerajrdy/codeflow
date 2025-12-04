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
## Architecture

CodeFlow uses a workflow-based orchestration pattern with specialized agents:

- **Design Agent**: Analyzes tickets and proposes implementation approaches
- **Coding Agent**: Generates code changes as patches/diffs
- **Review Agent**: Evaluates changes against acceptance criteria
- **Notes Agent**: Captures learnings and metadata


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

See [docs/design/design.md](docs/design/design.md) for the complete implementation plan.
