"""
Day 3 Demo: Coding Agent + Jira/GitHub integration (dry-run by default).

This script demonstrates the full workflow using real agents when GOOGLE_API_KEY
is available. Jira/GitHub clients are initialized from environment variables:
- JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY
- GITHUB_REPO, GITHUB_TOKEN, GITHUB_DEFAULT_BRANCH

By default, dry-run mode is enabled to avoid modifying your git working tree.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Add repo root to import path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import DesignAgent, CodingAgent, ReviewAgent  # noqa: E402
from src.integrations import JiraClient, GitHubClient  # noqa: E402
from src.models import GoogleGeminiClient  # noqa: E402
from src.orchestration import WorkflowEngine  # noqa: E402


async def main():
    """Run a demo workflow using available integrations."""
    dry_run = True  # Safe by default; set False to apply patches and run git
    ticket_id = os.getenv("CODEFLOW_TICKET", "DAY3-DEMO-001")
    api_key = os.getenv("GOOGLE_API_KEY")

    # Try gemini-1.5-flash which may be less restrictive
    default_model = "gemini-1.5-flash"

    jira_client = JiraClient(
        base_url=os.getenv("JIRA_BASE_URL"),
        email=os.getenv("JIRA_EMAIL"),
        api_token=os.getenv("JIRA_API_TOKEN"),
        project_key=os.getenv("JIRA_PROJECT_KEY"),
    )

    github_client = GitHubClient(
        repo=os.getenv("GITHUB_REPO"),
        token=os.getenv("GITHUB_TOKEN"),
        repo_path=str(Path(__file__).parent.parent.resolve()),
        default_branch=os.getenv("GITHUB_DEFAULT_BRANCH", "main"),
        dry_run=dry_run,
    )

    if api_key:
        print("✓ GOOGLE_API_KEY found - using real agents")
        model_client = GoogleGeminiClient(model_name=os.getenv("GOOGLE_MODEL", default_model))
        design_agent = DesignAgent(model_client)
        coding_agent = CodingAgent(model_client)
        review_agent = ReviewAgent(model_client)
        engine = WorkflowEngine(
            design_agent=design_agent,
            coding_agent=coding_agent,
            review_agent=review_agent,
            jira_client=jira_client,
            github_client=github_client,
        )
    else:
        print("⚠ No GOOGLE_API_KEY found - running in stub mode")
        engine = WorkflowEngine(
            jira_client=jira_client,
            github_client=github_client,
        )

    context = await engine.run(
        ticket_id=ticket_id,
        config={
            "repo_path": str(Path(__file__).parent.parent.resolve()),
            "test_command": os.getenv("TEST_COMMAND", "pytest"),
            "repo_url": os.getenv("REPO_URL", ""),
        },
        dry_run=dry_run,
    )

    print("\n" + "=" * 60)
    print("DAY 3 DEMO RESULTS")
    print("=" * 60)
    print(f"Ticket: {ticket_id}")
    print(f"Dry Run: {dry_run}")
    if context.design:
        print(f"- Design target files: {len(context.design.target_files)}")
    if context.coding:
        print(f"- Coding diff length: {len(context.coding.diff)} chars")
    if context.review:
        print(f"- Review decision: {context.review.decision}")
    if context.pr:
        print(f"- PR URL: {context.pr.pr_url}")
    print(f"Status: {'SUCCESS' if context.is_successful() else 'FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
