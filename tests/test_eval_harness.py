"""Tests for evaluation harness."""

import asyncio
from pathlib import Path

import pytest

from src.eval import run_evaluation_suite


@pytest.mark.asyncio
async def test_run_evaluation_suite_stub_mode(tmp_path, monkeypatch):
    """Evaluation suite should produce a report and summary in stub mode."""
    # Ensure stub mode by clearing API key
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    config_path = tmp_path / "config.yaml"
    runs_dir = tmp_path / "runs"
    config_path.write_text(
        f"workflow:\n  runs_dir: {runs_dir}\n  max_retries: 0\n", encoding="utf-8"
    )

    report = await run_evaluation_suite(
        tickets=["EVAL-1", "EVAL-2"],
        config_path=str(config_path),
        dry_run=True,
    )

    assert report["successes"] == 2
    assert report["failures"] == 0
    assert report["results"][0]["status"] == "success"

    # Report file should be written
    report_file = runs_dir / f"eval_{report['started_at']}.json"
    assert report_file.exists()
