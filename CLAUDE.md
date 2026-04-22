# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Octobots is a framework for orchestrating multiple Claude Code instances as an AI development team. It's installed into target projects as a sibling directory (`octobots/`), not run standalone. Roles (PM, dev, QA, BA, tech lead, scout) and most published skills now live in the single `arozumenko/sdlc-skills` monorepo and are installed via `npx github:arozumenko/sdlc-skills init --agents <name> --skills <name> --target claude`. Roles communicate through a shared SQLite queue (taskbox).

## Commands

```bash
# Validate infrastructure readiness
python3 octobots/scripts/check-spawn-ready.py
python3 octobots/scripts/check-spawn-ready.py --check infra-only
python3 octobots/scripts/check-spawn-ready.py --check files-only

# Check shell script syntax
bash -n octobots/scripts/*.sh

# Install Python dependencies
pip install -r octobots/scripts/requirements.txt

# Start a single role (interactive, from project root)
octobots/start.sh scout
octobots/start.sh python-dev

# Start full team (Rich TUI supervisor)
python3 octobots/scripts/supervisor.py

# Taskbox CLI
python octobots/skills/taskbox/scripts/relay.py send --from py --to pm "message"
python octobots/skills/taskbox/scripts/relay.py inbox --id pm
python octobots/skills/taskbox/scripts/relay.py ack MSG_ID "acked"

# Agent registry / team selector (non-interactive)
python3 octobots/scripts/select-agents.py --preset 0   # first preset
python3 octobots/scripts/select-agents.py --all        # all agents
```

There is no test suite for the framework itself — tests live in target projects.

## Architecture

### Role System (Decoupled)

Roles live in `arozumenko/sdlc-skills/agents/<name>/` (a few third-party agents like `onetest-ai/qa-agent` remain on their own). Each agent dir has:
- `AGENT.md` — YAML frontmatter (name, model, color, `workspace`, skills list) + technical instructions
- `SOUL.md` — Personality, voice, working style

Install a role: `npx github:arozumenko/sdlc-skills init --agents <name> --target claude`
Install several at once: `npx github:arozumenko/sdlc-skills init --agents ba,tech-lead,pm --target claude`

Role resolution order (both `start.sh` and `supervisor.py`):
1. `.octobots/roles/<role>/` (project overrides)
2. `.claude/agents/<role>/` (installed via `npx github:<repo> init`)

`octobots/roles/` is no longer a role source. The supervisor reads from
`.claude/agents/` directly — no promotion, no moving files out of user-owned
directories. `/role add <id>` / `/role add owner/repo[@ref]` installs into
`.claude/agents/` via `registry-fetch.sh` and then launches the worker in place.
`/role remove` only tears down `.octobots/workers/<role>/` and leaves
`.claude/agents/<role>/` intact — uninstall the agent separately if you want it
gone.

Roles with `workspace: clone` get isolated repo clones under `.octobots/workers/<role>/`.

### Agent Registry

`agents.json` lists all published agents and team presets. Used by:
- `install.sh` via `scripts/select-agents.py` for cookiecutter team setup
- Scout during project onboarding to propose team adjustments

```json
{
  "monorepo": { "id": "sdlc-skills", "repo": "arozumenko/sdlc-skills", "ref": "main" },
  "agents": [{
    "id": "scout", "monorepo": "sdlc-skills", "name": "scout", "required": true,
    "group": "core",
    "theme": {"color": "colour252", "icon": "🔍", "short_name": "scout"},
    "aliases": ["kit"]
  }, ...],
  "presets": [{ "name": "iOS development", "agents": [...], "qa": "qa-sage" }, ...]
}
```

Each agent's optional `group` (`core` | `dev` | `qa`) determines how
`select-agents.py` groups it in the Custom flow (core = y/n each, devs =
multi-select, qas = picker). `theme` drives the tmux pane styling in
supervisor.py (`ROLE_THEME` is loaded from this file at import time).
`aliases` drives shorthand resolution in `scripts/roles.py`
(`ROLE_ALIASES`/`ROLE_DISPLAY` are loaded from this file too). Adding a new
dev or QA is a one-file change — register it here with group/theme/aliases
and every consumer picks it up.

### Taskbox (Inter-Role Messaging)

All inter-role communication flows through a single SQLite database (`.octobots/relay.db`). No REST APIs, no MCP servers for messaging — just Python stdlib + Bash. The supervisor holds incoming messages until the worker acknowledges the current task, preventing pile-up.

### Session-Per-Issue Pattern

Each GitHub issue maps to a named Claude Code session (e.g., `python-dev-issue-103`). Roles use `/resume <session-name>` to restore full context when returning to a task. This keeps context isolated and prevents bloat.

### Three Communication Channels

| Channel | Purpose | Persistence |
|---|---|---|
| `board.md` | Team state — decisions, blockers, active work | Git-versioned |
| Taskbox | Task assignment, async nudges | SQLite, ephemeral |
| GitHub Issues | Permanent audit trail, every action commented | Permanent |

### Pipeline Flow

```
User → PM (Max) → BA (Alex): analyze requirements
BA → Tech Lead (Rio): epic + user stories
Tech Lead → PM: technical tasks
PM → Dev (Py/Jay): assignments
Dev → PM: PR created
PM → QA (Sage): verify PR
Any role → User: `notify` MCP tool → Telegram
```

### Supervisor (`scripts/supervisor.py`)

Rich TUI that manages tmux panes, polls taskbox, runs scheduled jobs, and maintains the team board. Key REPL commands:

```
/role list|add|remove|clone       # dynamic team management
/skill <role> <skill>             # add skill to running role
/schedule every 30m @pm <task>    # cron-style scheduling
/loop 10m @qa <task>              # recurring loop
```

### Skills System

Bundled skills in `skills/<name>/` are reusable capabilities symlinked into each role's `.claude/skills/`. Published skills (code-review, git-workflow, tdd, memory, etc.) live in `arozumenko/sdlc-skills/skills/<name>/` and are installed via `npx github:arozumenko/sdlc-skills init --skills <name> --target claude`. The `SKILL.md` file defines the skill per the agentskills.io spec.

Bundled skills (still in this repo):
- `taskbox` — inter-role messaging relay
- `memory` — per-role persistent memory; supervisor invokes `memory.py snapshot` at every role launch
- `bugfix-workflow` — structured bug investigation
- `implement-feature` — feature implementation workflow
- `plan-feature` — feature planning workflow
- `project-seeder` — scout's project configuration skill

Shared agents in `shared/agents/`:
- `taskbox-listener` — long-running inbox poller
- `issue-reproducer` — reproduces GitHub issues
- `rca-investigator` — root cause analysis

### Worker Environments

`scripts/init-project.sh` sets up `.octobots/workers/<role>/` for each discovered role. Each worker gets:
- Symlinks to shared resources (`octobots/`, `.octobots/`, `.env`, etc.)
- `.claude/agents/<role>/` — symlink to the role's agent dir
- `.claude/skills/` — symlinks to allowed skills (filtered by `skills:` in AGENT.md)
- `OCTOBOTS.md` — generated per-worker config (Worker ID, taskbox commands, memory path)
- `CLAUDE.md` — imports `@shared/conventions.md` + `@OCTOBOTS.md` (written once, user-editable)

Clone workers (`workspace: clone`) additionally get isolated git clones for each repo.

### Runtime Directory (`.octobots/`)

Created by `scripts/init-project.sh` in the target project, not in the octobots repo itself:
- `board.md` — Team board (auto-created if missing)
- `relay.db` — SQLite taskbox
- `memory/` — Per-role MEMORY.md files
- `workers/` — Isolated worker environments
- `schedule.json` — Persistent scheduled jobs

## Key Conventions

**Terminal Rules (Critical):** Roles run in unattended tmux panes. They must never ask questions to stdout or present options and wait. All user communication goes through the `notify` MCP tool (`mcp__notify__notify`, defined in `mcp/notify/server.py` and registered in `.mcp.json`). The transport logic lives in `scripts/notify_lib.py` and is shared with the supervisor's own internal warnings. All teammate communication goes through taskbox.

**Three-Step Task Completion (mandatory for all roles):**
1. Comment on GitHub issue with results
2. Ack the taskbox message
3. Notify user via the `notify` MCP tool

Skipping any step breaks the pipeline.

**GitHub Labels Track Status:** `ready` → `in-progress` → `review` → `testing` → `done`. Before starting a task, check for `in-progress` label to avoid duplicate work.

## Configuration

`.env.octobots` (in target project root, not in this repo):
```bash
OCTOBOTS_TG_TOKEN=...         # Telegram bot token
OCTOBOTS_TG_OWNER=...         # Telegram user ID for notifications
OCTOBOTS_WORKERS=project-manager python-dev js-dev qa-engineer ba tech-lead
OCTOBOTS_EXCLUDED_ROLES=scout
```

`.mcp.json` configures MCP servers available to all roles: Playwright, GitHub, Context7, Tavily (web search), Accessibility Scanner, Lighthouse.

## Adding a New Role

1. Add `agents/<name>/AGENT.md` (with YAML frontmatter) and `agents/<name>/SOUL.md` to `arozumenko/sdlc-skills`
2. Register in `agents.json` under `"agents"` with `monorepo: sdlc-skills` and `name: <name>`. Add:
   - `role: <name>` — the worker id at runtime (must match the dir the installer drops into)
   - `group: "core" | "dev" | "qa"` — where it appears in the Custom selector
   - `theme: {color, icon, short_name}` — tmux pane styling
   - `aliases: [short, nickname, ...]` — @shorthand resolution (e.g. `["io", "ios"]` for ios-dev)
3. Use `workspace: clone` in AGENT.md frontmatter if the role needs an isolated repo clone
4. No Python changes required — `supervisor.py`, `scripts/roles.py`, and `scripts/select-agents.py`
   all read the registry at startup.

## Adding a New Skill

Follow the agentskills.io spec documented in `docs/skill-spec.md`. The `SKILL.md` file is the definition. Scripts go in `skills/<name>/scripts/`. The skill is activated by symlinking into a role's `.claude/skills/`.

For published skills: add to `arozumenko/sdlc-skills/skills/<name>/` and register in `skills.json` with `monorepo: sdlc-skills`.
For bundled skills (framework-internal, e.g. taskbox): add to `skills/<name>/` in this repo.
