"""Configuration loader for CodeFlow."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


DEFAULTS = {
    "repo_path": str(Path().resolve()),
    "main_language": "Python",
    "test_command": "pytest",
    "repo_url": "",
    "default_branch": "main",
    "max_retries": 1,
    "runs_dir": "runs",
    "auto_confirm": False,
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file if present, with sane defaults.

    Precedence:
    1. Explicit path provided via CLI.
    2. config.yaml in project root.
    3. Defaults (with some env overrides).
    """
    config: Dict[str, Any] = {}

    path = Path(config_path) if config_path else Path("config.yaml")
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                if isinstance(loaded, dict):
                    config.update(loaded)
        except Exception as exc:
            print(f"Warning: unable to load config from {path}: {exc}")

    # Apply defaults where missing
    merged = {**DEFAULTS, **config}

    # Normalize nested sections
    test_cfg = config.get("test") if isinstance(config.get("test"), dict) else {}
    merged["test_command"] = test_cfg.get("command", merged["test_command"])

    workflow_cfg = config.get("workflow") if isinstance(config.get("workflow"), dict) else {}
    merged["max_retries"] = workflow_cfg.get("max_retries", merged["max_retries"])
    merged["runs_dir"] = workflow_cfg.get("runs_dir", merged.get("runs_dir", "runs"))
    merged["auto_confirm"] = workflow_cfg.get("auto_confirm", merged.get("auto_confirm", False))

    github_cfg = config.get("github") if isinstance(config.get("github"), dict) else {}
    merged["repo_url"] = github_cfg.get("repo_url", merged["repo_url"])
    merged["default_branch"] = github_cfg.get("default_branch", merged["default_branch"])

    # Environment overrides (optional)
    merged["repo_path"] = os.getenv("REPO_PATH", merged["repo_path"])
    merged["test_command"] = os.getenv("TEST_COMMAND", merged["test_command"])
    merged["repo_url"] = os.getenv("REPO_URL", merged["repo_url"])
    merged["default_branch"] = os.getenv("GITHUB_DEFAULT_BRANCH", merged["default_branch"])

    # Boolean env override for auto_confirm
    auto_confirm_env = os.getenv("CODEFLOW_AUTO_CONFIRM")
    if auto_confirm_env is not None:
        merged["auto_confirm"] = auto_confirm_env.lower() in ("1", "true", "yes", "y")

    return merged
