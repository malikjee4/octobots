#!/usr/bin/env python3
"""CLI bridge for creating durable supervisor-scheduled jobs from within a role.

Roles call this via the Bash tool to register open loops and recurring tasks
that survive session restarts. The supervisor picks up changes on its next
poll cycle (every ~15s) — no restart needed.

Usage:
    # Create a recurring job
    python3 octobots/scripts/schedule-job.py create \\
        --type every --spec 1d \\
        --action prompt --target pa \\
        --content "Open loop follow-up: revisit auth approach decision"

    # Create a one-shot job at a specific time
    python3 octobots/scripts/schedule-job.py create \\
        --type at --spec 2026-04-11 \\
        --action prompt --target pa \\
        --content "Follow up: John's proposal review"

    # Create a cron job
    python3 octobots/scripts/schedule-job.py create \\
        --type cron --spec "0 9 * * MON-FRI" \\
        --action send --target pm \\
        --content "Week {week} standup — review all in-progress issues"

    # List all durable jobs
    python3 octobots/scripts/schedule-job.py list

    # Delete a job by ID
    python3 octobots/scripts/schedule-job.py delete JOB_ID
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add the scripts directory to sys.path so we can import scheduler.py
_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from scheduler import (
    JobAction,
    JobStore,
    JobType,
    ScheduledJob,
    next_cron_run,
    parse_at_time,
    parse_interval,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _resolve_schedule_json() -> Path:
    """Find .octobots/schedule.json relative to CWD or via env var."""
    db = os.environ.get("OCTOBOTS_DB")
    if db:
        runtime = Path(db).parent
    else:
        runtime = Path.cwd() / ".octobots"
    return runtime / "schedule.json"


def _compute_next_run(job_type: JobType, spec: str) -> str:
    now = datetime.now(timezone.utc)
    if job_type == JobType.AT:
        return parse_at_time(spec).isoformat()
    elif job_type == JobType.EVERY:
        return (now + parse_interval(spec)).isoformat()
    elif job_type == JobType.CRON:
        return next_cron_run(spec, now).isoformat()
    raise ValueError(f"Unknown job type: {job_type}")


# ── Subcommands ───────────────────────────────────────────────────────────────


def cmd_create(args: argparse.Namespace) -> int:
    try:
        job_type = JobType(args.type)
    except ValueError:
        print(f"Error: invalid --type '{args.type}'. Use: at, every, cron", file=sys.stderr)
        return 1

    try:
        job_action = JobAction(args.action)
    except ValueError:
        print(f"Error: invalid --action '{args.action}'. Use: send, prompt, run, agent", file=sys.stderr)
        return 1

    try:
        next_run = _compute_next_run(job_type, args.spec)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    job = ScheduledJob(
        id=uuid.uuid4().hex[:8],
        type=job_type,
        spec=args.spec,
        action=job_action,
        target=args.target,
        content=args.content,
        created_at=datetime.now(timezone.utc).isoformat(),
        next_run=next_run,
        last_run=None,
        paused=False,
        run_count=0,
    )

    schedule_path = _resolve_schedule_json()
    store = JobStore(schedule_path)
    store.add(job)

    result = {"id": job.id, "status": "created", "fires": next_run}
    print(json.dumps(result))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    schedule_path = _resolve_schedule_json()
    store = JobStore(schedule_path)
    jobs = store.load()

    if not jobs:
        print("No scheduled jobs.")
        return 0

    # Header
    col = "{:<10} {:<6} {:<18} {:<10} {:<20} {}"
    print(col.format("ID", "TYPE", "SPEC", "TARGET", "NEXT RUN", "CONTENT"))
    print("-" * 90)

    for j in jobs:
        next_run = j.next_run[:16] if j.next_run else "—"
        content_preview = j.content[:40] + "…" if len(j.content) > 40 else j.content
        paused_mark = " [paused]" if j.paused else ""
        print(col.format(
            j.id,
            j.type.value,
            j.spec[:18],
            j.target[:10],
            next_run,
            content_preview + paused_mark,
        ))

    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    schedule_path = _resolve_schedule_json()
    store = JobStore(schedule_path)

    if not store.remove(args.job_id):
        print(f"Error: job '{args.job_id}' not found.", file=sys.stderr)
        return 1

    print(json.dumps({"id": args.job_id, "status": "deleted"}))
    return 0


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="schedule-job.py",
        description="Create, list, or delete durable supervisor-scheduled jobs.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # create
    c = sub.add_parser("create", help="Create a new scheduled job")
    c.add_argument("--type", required=True, choices=["at", "every", "cron"],
                   help="Job type: 'at' (one-shot), 'every' (recurring), 'cron' (cron expression)")
    c.add_argument("--spec", required=True,
                   help="Time spec: '2026-04-11' / '15:00' / '2h' / '30m' / '0 9 * * MON-FRI'")
    c.add_argument("--action", required=True, choices=["send", "prompt", "run", "agent"],
                   help="Action: 'send' (taskbox), 'prompt' (tmux keys), 'run' (shell), 'agent' (Claude Code)")
    c.add_argument("--target", required=True,
                   help="Target role name (send/prompt/agent) or shell command (run)")
    c.add_argument("--content", required=True,
                   help="Message content. Supports {time}, {date}, {weekday}, {role}, {schedule}, etc.")

    # list
    sub.add_parser("list", help="List all scheduled jobs")

    # delete
    d = sub.add_parser("delete", help="Delete a job by ID")
    d.add_argument("job_id", help="Job ID (from 'create' output or 'list')")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        return cmd_create(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "delete":
        return cmd_delete(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
