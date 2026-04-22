"""Shared role aliases and display names for Octobots.

Used by supervisor, telegram-bridge, and scheduler to resolve
@shorthand → full role names consistently.

All runtime metadata (aliases, display icons, theme colors) is loaded
from each installed agent's AGENT.md frontmatter via `agent_registry.py`
and overlaid with octobots/agent-overrides.json for agents that don't
ship those fields. Adding a new agent to the team requires zero changes
to this module.
"""
from __future__ import annotations

from agent_registry import role_aliases


ROLE_ALIASES, ROLE_DISPLAY = role_aliases()


def resolve_alias(name: str) -> str:
    """Resolve a role alias to the canonical role name.

    Returns the input unchanged if not a known alias.
    """
    return ROLE_ALIASES.get(name.lower(), name)
