"""Tests for config loader."""

import os
from pathlib import Path

from src.config import load_config


def test_load_config_defaults(tmp_path, monkeypatch):
    """Config should use defaults when no file is present."""
    cwd = tmp_path
    monkeypatch.chdir(cwd)

    config = load_config()

    assert config["test_command"] == "pytest"
    assert config["max_retries"] == 1
    assert config["runs_dir"] == "runs"


def test_load_config_file(tmp_path, monkeypatch):
    """Config file should override defaults."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "test_command: npm test\nmax_retries: 2\nrepo_url: https://example.com\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config["test_command"] == "npm test"
    assert config["max_retries"] == 2
    assert config["repo_url"] == "https://example.com"


def test_load_config_env_override(monkeypatch):
    """Environment variables should override loaded values."""
    monkeypatch.setenv("TEST_COMMAND", "make test")
    config = load_config()
    assert config["test_command"] == "make test"

