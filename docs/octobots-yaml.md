# octobots.yaml — Project Composition File

`octobots.yaml` lives in your **project root** (alongside `.env.octobots`). It declares the exact roles and skills your project uses, with optional version pins. Check it into git for reproducibility.

## Format

```yaml
version: "1.0"

roles:
  - repo: sdlc:project-manager      # → sdlc-skills monorepo, agent "project-manager"
  - repo: sdlc:python-dev
  - repo: sdlc:qa-engineer
  - repo: myorg/custom-agent        # private or unlisted third-party agent
    ref: main

skills:
  - repo: sdlc:tdd                  # → sdlc-skills monorepo, skill "tdd"
  - repo: sdlc:code-review
  - repo: sdlc:msgraph
  - repo: myorg/skill-internal      # private skill on its own repo
    ref: feature/new-workflow
```

The `sdlc:<name>` shorthand resolves through the `arozumenko/sdlc-skills` monorepo installer in one batched call. Plain `owner/repo[@ref]` entries still install individually for third-party agent / skill repos.

## Fields

| Field | Required | Description |
|---|---|---|
| `version` | No | Schema version (`"1.0"`) |
| `roles[].repo` | Yes | GitHub repo in `owner/repo` format |
| `roles[].ref` | No | Branch, tag, or SHA. Default: `main` |
| `skills[].repo` | Yes | GitHub repo in `owner/repo` format |
| `skills[].ref` | No | Branch, tag, or SHA. Default: `main` |

## How init-project.sh uses it

```bash
# First init — fetches declared roles + skills
octobots/scripts/init-project.sh

# Re-fetch everything at their declared refs (update)
octobots/scripts/init-project.sh --update

# Add one role ad-hoc (not in octobots.yaml)
octobots/scripts/init-project.sh --role sdlc:scout
octobots/scripts/init-project.sh --role myorg/custom-agent@v2.0

# Add one skill ad-hoc
octobots/scripts/init-project.sh --skill sdlc:msgraph
```

## Fetch strategy

For each declared role or skill, `registry-fetch.sh` tries in order:

1. **`sdlc:<name>`** → `npx github:arozumenko/sdlc-skills init --agents/--skills <name> --target claude --yes`
2. **`npx github:<repo> init --all`** (roles) or **`npx skills add <repo>`** (skills) — uses the agentskills.io/npx ecosystem, installs into `.claude/agents/` or `.claude/skills/`
3. **`git clone --depth 1 --branch <ref>`** fallback — clones into `.octobots/registry/<repo-name>/`, then symlinks into `.claude/agents/<name>/` or `.claude/skills/<name>/`

The git clone fallback works for private repos and repos not published to npm.

## What stays bundled

These octobots-internal skills are **not** declared in `octobots.yaml` — they are symlinked unconditionally by `init-project.sh`:

- `skills/taskbox/` — inter-role messaging infrastructure
- `skills/bugfix-workflow/` — structured bug investigation
- `skills/implement-feature/` — feature implementation workflow
- `skills/plan-feature/` — feature planning workflow
- `skills/project-seeder/` — scout's project configuration skill

## Runtime: supervisor REPL

```
/role add scout                          # look up in agents.json → sdlc-skills
/role add sdlc:scout                     # explicit sdlc-skills form
/role add myorg/custom-agent@v2.0        # third-party repo (still supported)
/skill add sdlc:msgraph                  # fetch + link into all active workers
/skill add myorg/skill-internal@main     # private skill via git clone fallback
```

## .gitignore

The fetched content lives in `.octobots/registry/` and `.claude/` — both gitignored. `octobots.yaml` itself should be committed:

```gitignore
# These are gitignored by install.sh:
octobots/
.octobots/
.claude/
.env.octobots

# Commit this:
# octobots.yaml
```
