"""Persistence utilities for workflow runs."""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _serialize(value: Any) -> Any:
    """Convert dataclass/datetime objects into JSON-friendly structures."""
    if is_dataclass(value):
        return {k: _serialize(v) for k, v in asdict(value).items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    return value


def save_run(context, runs_dir: str = "runs") -> Path:
    """Persist a workflow run to disk as JSON."""
    runs_path = Path(runs_dir)
    runs_path.mkdir(parents=True, exist_ok=True)

    run_data: Dict[str, Any] = {
        "run_id": context.run_id,
        "ticket": _serialize(context.ticket),
        "repo": _serialize(context.repo),
        "design": _serialize(context.design),
        "coding": _serialize(context.coding),
        "test": _serialize(context.test),
        "review": _serialize(context.review),
        "pr": _serialize(context.pr),
        "notes": _serialize(context.notes),
        "completed_steps": context.completed_steps,
        "errors": context.errors,
        "logs": context.logs,
        "started_at": _serialize(context.started_at),
        "completed_at": _serialize(context.completed_at),
        "dry_run": context.dry_run,
    }

    file_path = runs_path / f"{context.run_id}.json"
    file_path.write_text(json.dumps(run_data, indent=2), encoding="utf-8")
    return file_path


def list_runs(runs_dir: str = "runs") -> List[Dict[str, Any]]:
    """List saved runs with minimal metadata."""
    runs_path = Path(runs_dir)
    if not runs_path.exists():
        return []

    runs = []
    for path in sorted(runs_path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            runs.append(
                {
                    "run_id": data.get("run_id", path.stem),
                    "ticket_id": data.get("ticket", {}).get("ticket_id"),
                    "completed_at": data.get("completed_at"),
                    "status": "success" if not data.get("errors") else "failed",
                    "pr_url": (data.get("pr") or {}).get("pr_url"),
                }
            )
        except json.JSONDecodeError:
            continue
    return runs


def load_run(run_id: str, runs_dir: str = "runs") -> Dict[str, Any]:
    """Load a saved run by ID."""
    path = Path(runs_dir) / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Run {run_id} not found in {runs_dir}")
    return json.loads(path.read_text(encoding="utf-8"))
