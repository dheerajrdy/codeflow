"""Evaluation harness to run CodeFlow across multiple tickets and collect metrics."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agents import DesignAgent, CodingAgent, ReviewAgent, NotesAgent
from src.config import load_config
from src.integrations import GitHubClient, JiraClient
from src.models import GoogleGeminiClient
from src.orchestration import WorkflowEngine


async def _build_engine(dry_run: bool, auto_confirm: bool) -> WorkflowEngine:
    """Create a WorkflowEngine with integrations and agents if credentials exist."""
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
            model_client = GoogleGeminiClient(model_name=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"))
            return WorkflowEngine(
                design_agent=DesignAgent(model_client),
                coding_agent=CodingAgent(model_client),
                review_agent=ReviewAgent(model_client),
                notes_agent=NotesAgent(model_client),
                jira_client=jira_client,
                github_client=github_client,
                auto_confirm=auto_confirm,
            )
        except Exception:
            # Fall back to stub agents if model cannot be initialized
            pass

    return WorkflowEngine(
        jira_client=jira_client,
        github_client=github_client,
        auto_confirm=auto_confirm,
    )


async def _run_single(ticket: str, config: Dict[str, Any], dry_run: bool, auto_confirm: bool):
    """Run the workflow for a single ticket and return context."""
    engine = await _build_engine(dry_run=dry_run, auto_confirm=auto_confirm)
    return await engine.run(ticket_id=ticket, config={**config, "ticket_id": ticket}, dry_run=dry_run)


def _summarize_context(context) -> Dict[str, Any]:
    """Extract evaluation-friendly summary from WorkflowContext."""
    return {
        "run_id": context.run_id,
        "ticket_id": context.ticket.ticket_id if context.ticket else None,
        "status": "success" if context.is_successful() else "failed",
        "errors": context.errors,
        "pr_url": context.pr.pr_url if context.pr else None,
        "review_decision": context.review.decision if context.review else None,
        "tests_passed": context.test.success if context.test else False,
        "duration_seconds": (context.completed_at - context.started_at).total_seconds()
        if context.completed_at
        else None,
    }


def _write_report(report: Dict[str, Any], runs_dir: str) -> Path:
    """Persist evaluation report to disk."""
    runs_path = Path(runs_dir)
    runs_path.mkdir(parents=True, exist_ok=True)
    file_path = runs_path / f"eval_{report['started_at']}.json"
    file_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return file_path


async def run_evaluation_suite(
    tickets: List[str],
    config_path: Optional[str] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Run CodeFlow across multiple tickets and return aggregated metrics.

    Args:
        tickets: list of ticket IDs to process
        config_path: optional path to config.yaml
        dry_run: run in dry-run mode (recommended for evaluation)
    """
    config = load_config(config_path)
    auto_confirm = config.get("auto_confirm", False)
    runs_dir = config.get("runs_dir", "runs")

    started_at = datetime.now().strftime("%Y%m%d-%H%M%S")
    results = []

    for ticket in tickets:
        ctx = await _run_single(ticket, config, dry_run, auto_confirm)
        results.append(_summarize_context(ctx))

    successes = sum(1 for r in results if r["status"] == "success")
    report = {
        "started_at": started_at,
        "tickets": tickets,
        "dry_run": dry_run,
        "successes": successes,
        "failures": len(results) - successes,
        "success_rate": successes / len(results) if results else 0.0,
        "results": results,
    }

    report_path = _write_report(report, runs_dir=runs_dir)
    print(f"Evaluation report saved to {report_path}")
    return report
