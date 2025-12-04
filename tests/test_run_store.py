"""Tests for run persistence utilities."""

from datetime import datetime

from src.orchestration.context import WorkflowContext, TicketInfo, PRInfo
from src.orchestration.run_store import save_run, list_runs, load_run


def test_save_and_load_run(tmp_path):
    """Saving a run should create a JSON file that can be loaded/listed."""
    context = WorkflowContext(run_id="run123")
    context.ticket = TicketInfo(ticket_id="T-1", title="Test ticket")
    context.pr = PRInfo(branch_name="feature/T-1", pr_url="https://example.com/pr/1")
    context.completed_at = datetime.now()
    context.logs.append("START Test")

    save_run(context, runs_dir=tmp_path)

    runs = list_runs(runs_dir=tmp_path)
    assert len(runs) == 1
    assert runs[0]["run_id"] == "run123"
    assert runs[0]["ticket_id"] == "T-1"

    loaded = load_run("run123", runs_dir=tmp_path)
    assert loaded["ticket"]["ticket_id"] == "T-1"
    assert loaded["pr"]["pr_url"] == "https://example.com/pr/1"
