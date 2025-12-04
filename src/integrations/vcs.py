"""Local repository helpers for applying patches and running tests."""

import shlex
import subprocess
import time
from typing import Tuple


def apply_patch(repo_path: str, diff: str, dry_run: bool = False) -> Tuple[bool, str]:
    """
    Apply a unified diff to the repository using git apply.

    Returns:
        success flag and combined stdout/stderr output.
    """
    if not diff or not diff.strip():
        return False, "No diff provided"

    if dry_run:
        return True, "Skipped apply (dry-run mode)"

    result = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        input=diff.encode("utf-8"),
        cwd=repo_path,
        capture_output=True,
    )

    output = (result.stdout or b"").decode() + (result.stderr or b"").decode()
    return result.returncode == 0, output.strip()


def run_tests(repo_path: str, command: str, dry_run: bool = False) -> Tuple[bool, str, str, float]:
    """
    Run the project's test command.

    Returns:
        success flag, stdout, stderr, duration_seconds
    """
    if dry_run:
        return True, "[DRY RUN] Tests skipped", "", 0.0

    if not command:
        return True, "No test command configured", "", 0.0

    start = time.time()
    result = subprocess.run(
        shlex.split(command),
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    duration = time.time() - start

    return result.returncode == 0, result.stdout, result.stderr, duration
