"""Tests for integration helpers and clients."""

import pytest

from src.integrations import JiraClient, GitHubClient, run_tests


@pytest.mark.asyncio
async def test_jira_client_stub_returns_ticket():
    """JiraClient should return stubbed data when not configured."""
    client = JiraClient()
    ticket = await client.fetch_ticket("TEST-123")

    assert ticket.ticket_id == "TEST-123"
    assert ticket.raw_data  # should include stub marker
    assert ticket.title.startswith("[STUB]") or ticket.raw_data.get("stub")


@pytest.mark.asyncio
async def test_github_client_dry_run_pr():
    """GitHubClient should avoid network calls in dry-run mode."""
    client = GitHubClient(repo="example/repo", dry_run=True)

    # No exceptions should be raised in dry-run mode
    await client.create_branch("feature/TEST-1")
    await client.commit_all("TEST-1: commit message")
    await client.push_branch("feature/TEST-1")

    pr_info = await client.create_pull_request(
        branch_name="feature/TEST-1",
        title="TEST-1: demo",
        body="body",
    )

    assert pr_info.branch_name == "feature/TEST-1"
    assert "github.com" in pr_info.pr_url


def test_run_tests_dry_run(tmp_path):
    """run_tests should short-circuit in dry-run mode."""
    success, output, errors, duration = run_tests(str(tmp_path), "echo ok", dry_run=True)

    assert success is True
    assert "DRY RUN" in output
    assert errors == ""
    assert duration == 0.0
