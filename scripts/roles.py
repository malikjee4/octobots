"""Shared role aliases and display names for Octobots.

Used by supervisor, telegram-bridge, and scheduler to resolve
@shorthand → full role names consistently.

Both tables are loaded from agents.json at import time, so adding a new
agent (dev, QA, or otherwise) only requires editing the registry — no
code changes needed in this module.
"""
from __future__ import annotations

import json
from pathlib import Path


REGISTRY = Path(__file__).parent.parent / "agents.json"

# Broadcast aliases stay hardcoded — they aren't tied to individual agents.
_BROADCAST_ALIASES: dict[str, str] = {
    "all": "all",
    "everyone": "all",
    "team": "all",
}


def _load() -> tuple[dict[str, str], dict[str, str]]:
    aliases: dict[str, str] = dict(_BROADCAST_ALIASES)
    display: dict[str, str] = {}
    try:
        registry = json.loads(REGISTRY.read_text())
    except (OSError, ValueError):
        return aliases, display
    for agent in registry.get("agents", []):
        role = agent.get("role")
        if not role:
            continue
        aliases[role] = role
        for alias in agent.get("aliases", []) or []:
            aliases[alias] = role
        theme = agent.get("theme") or {}
        icon = theme.get("icon", "🤖")
        short = theme.get("short_name", role)
        display[role] = f"{icon} {short}"
    return aliases, display


ROLE_ALIASES, ROLE_DISPLAY = _load()


def resolve_alias(name: str) -> str:
    """Resolve a role alias to the canonical role name.

    Returns the input unchanged if not a known alias.
    """
    return ROLE_ALIASES.get(name.lower(), name)
