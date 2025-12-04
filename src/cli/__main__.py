"""CLI entrypoint for running workflows."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agents import DesignAgent, CodingAgent, ReviewAgent, NotesAgent
from src.integrations import JiraClient, GitHubClient
from src.models import GoogleGeminiClient
from src.orchestration import WorkflowEngine
from src.orchestration.run_store import list_runs, load_run
from src.config import load_config

# Load environment variables for integrations
load_dotenv()


def build_workflow_engine(dry_run: bool, auto_confirm: bool) -> WorkflowEngine:
    """Construct a WorkflowEngine with available agents and integrations."""
    jira_client = JiraClient(
        base_url=os.getenv("JIRA_BASE_URL"),
        email=os.getenv("JIRA_EMAIL"),
        api_token=os.getenv("JIRA_API_TOKEN"),
        project_key=os.getenv("JIRA_PROJECT_KEY"),
    )

    github_client = GitHubClient(
        repo=os.getenv("GITHUB_REPO"),
        token=os.getenv("GITHUB_TOKEN"),
        repo_path=os.getenv("REPO_PATH", str(Path().resolve())),
        default_branch=os.getenv("GITHUB_DEFAULT_BRANCH", "main"),
        dry_run=dry_run,
    )

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            model_client = GoogleGeminiClient(model_name=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp"))
            design_agent = DesignAgent(model_client)
            coding_agent = CodingAgent(model_client)
            review_agent = ReviewAgent(model_client)
            notes_agent = NotesAgent(model_client)

            print("✓ GOOGLE_API_KEY detected - using real agents")

            return WorkflowEngine(
                design_agent=design_agent,
                coding_agent=coding_agent,
                review_agent=review_agent,
                jira_client=jira_client,
                github_client=github_client,
                notes_agent=notes_agent,
                auto_confirm=auto_confirm,
            )
        except Exception as exc:  # pragma: no cover - import guard
            print(f"⚠️  Unable to initialize Google model client ({exc}); falling back to stub agents")

    print("Using stub agents (no GOOGLE_API_KEY provided)")
    return WorkflowEngine(
        jira_client=jira_client,
        github_client=github_client,
        notes_agent=None,
        auto_confirm=auto_confirm,
    )


async def run_workflow(ticket_id: str, dry_run: bool = False) -> int:
    """Run the workflow for a given ticket."""
    cli_config = load_config(os.getenv("CODEFLOW_CONFIG") or None)
    auto_confirm = cli_config.get("auto_confirm", False)

    engine = build_workflow_engine(dry_run=dry_run, auto_confirm=auto_confirm)

    try:
        context = await engine.run(
            ticket_id=ticket_id,
            config=cli_config,
            dry_run=dry_run,
        )

        # Return 0 for success, 1 for failure
        return 0 if context.is_successful() else 1

    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="CodeFlow: Multi-agent workflow for automated code changes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--ticket",
        help="Jira ticket ID (e.g., PROJ-123)",
    )
    group.add_argument(
        "--list-runs",
        action="store_true",
        help="List saved workflow runs",
    )
    group.add_argument(
        "--show-run",
        help="Show a specific run by ID",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making actual changes (no git operations)",
    )

    parser.add_argument(
        "--config",
        help="Path to config.yaml (defaults to ./config.yaml if present)",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-confirm git/PR actions (disables interactive guardrails)",
    )

    args = parser.parse_args()

    if args.list_runs:
        runs = list_runs()
        if not runs:
            print("No runs found.")
            sys.exit(0)
        for run in runs:
            print(
                f"{run['run_id']} | ticket={run.get('ticket_id')} | status={run.get('status')} | "
                f"completed_at={run.get('completed_at')} | pr={run.get('pr_url') or 'n/a'}"
            )
        sys.exit(0)

    if args.show_run:
        try:
            run = load_run(args.show_run)
        except FileNotFoundError as exc:
            print(str(exc))
            sys.exit(1)

        print(json.dumps(run, indent=2))
        sys.exit(0)

    if not args.ticket:
        parser.print_help()
        sys.exit(1)

    # Allow overriding config path at runtime
    if args.config:
        os.environ["CODEFLOW_CONFIG"] = args.config
    if args.yes:
        os.environ["CODEFLOW_AUTO_CONFIRM"] = "1"

    # Run the workflow
    exit_code = asyncio.run(run_workflow(args.ticket, args.dry_run))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
