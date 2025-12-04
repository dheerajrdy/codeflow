"""Minimal GitHub client for branch, commit, and PR creation."""

import asyncio
import os
import shlex
import subprocess
from typing import Optional

from src.orchestration.context import PRInfo

try:
    import requests  # type: ignore

    REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover - handled in code
    REQUESTS_AVAILABLE = False


class GitHubClient:
    """
    Lightweight GitHub client that shells out to git for local actions
    and uses the REST API for PR creation.
    """

    def __init__(
        self,
        repo: Optional[str] = None,
        token: Optional[str] = None,
        repo_path: str = ".",
        default_branch: str = "main",
        dry_run: bool = False,
    ):
        """
        Args:
            repo: "owner/repo" string
            token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
            repo_path: Local path to repository
            default_branch: Base branch for new branches/PRs
            dry_run: If True, skip git/network operations
        """
        self.repo = repo or os.getenv("GITHUB_REPO")
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo_path = repo_path
        self.default_branch = default_branch
        self.api_base = "https://api.github.com"
        self.dry_run = dry_run

        self.enabled = bool(self.repo and self.token and REQUESTS_AVAILABLE)

    async def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> None:
        """Create or reset a local branch."""
        if self.dry_run:
            return

        base = base_branch or self.default_branch
        await asyncio.to_thread(self._run_cmd, f"git fetch origin {base}", allow_failure=True)
        await asyncio.to_thread(self._run_cmd, f"git checkout -B {branch_name} origin/{base}")

    async def commit_all(self, message: str) -> None:
        """Stage and commit all changes."""
        if self.dry_run:
            return

        await asyncio.to_thread(self._run_cmd, "git add -A")
        # Allow empty commit to avoid failures when there are no changes
        await asyncio.to_thread(self._run_cmd, f"git commit --allow-empty -m {shlex.quote(message)}", allow_failure=True)

    async def push_branch(self, branch_name: str) -> None:
        """Push branch to origin."""
        if self.dry_run:
            return

        await asyncio.to_thread(self._run_cmd, f"git push -u origin {branch_name}")

    async def create_pull_request(self, branch_name: str, title: str, body: str) -> PRInfo:
        """Create a PR on GitHub or return a stub if not configured."""
        if self.dry_run or not self.enabled:
            pr_url = f"https://github.com/{self.repo or 'example/repo'}/pulls/{branch_name}"
            return PRInfo(branch_name=branch_name, pr_url=pr_url, pr_number=None)

        url = f"{self.api_base}/repos/{self.repo}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "title": title,
            "head": branch_name,
            "base": self.default_branch,
            "body": body,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        return PRInfo(
            branch_name=branch_name,
            pr_url=data.get("html_url", ""),
            pr_number=data.get("number"),
        )

    def _run_cmd(self, command: str, allow_failure: bool = False) -> None:
        """Run a shell command within the repository."""
        result = subprocess.run(
            command,
            cwd=self.repo_path,
            shell=True,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 and not allow_failure:
            raise RuntimeError(
                f"Command failed: {command}\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
