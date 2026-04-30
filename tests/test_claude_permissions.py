"""Tests for Claude Code permission flag selection."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from supervisor import claude_permission_args  # noqa: E402


def test_claude_bypass_permissions_enabled_by_default(monkeypatch):
    monkeypatch.delenv("OCTOBOTS_CLAUDE_BYPASS_PERMISSIONS", raising=False)

    assert claude_permission_args() == "--dangerously-skip-permissions"


def test_claude_bypass_permissions_can_be_disabled(monkeypatch):
    monkeypatch.setenv("OCTOBOTS_CLAUDE_BYPASS_PERMISSIONS", "0")

    assert claude_permission_args() == ""
