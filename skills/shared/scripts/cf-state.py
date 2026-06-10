#!/usr/bin/env python3
"""Read and mutate code-forge state.json deterministically.

Subcommands:
  show <state.json>                       Compact human summary + recomputed progress
  next <state.json>                       Print the next runnable pending task (deps satisfied)
  set-status <state.json> <task> <status> Set a task status, fix timestamps, recompute progress
  recompute <state.json>                  Recompute progress + overall status, write back
  init --feature NAME [...]               Scaffold a new state.json (tasks via stdin JSON)

Status values: pending | in_progress | completed | skipped | blocked
Timestamps are UTC ISO-8601 (e.g. 2026-06-10T12:00:00Z).

`init` reads a JSON array of task objects from stdin, e.g.:
  [{"id": "setup", "title": "Project setup", "dependencies": [],
    "estimated_hours": 2, "file": "tasks/setup.md"}]
Only `id` and `title` are required; the rest default sensibly.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_common as cf

_STATUS_ICON = {
    "pending": "[ ]",
    "in_progress": "[>]",
    "completed": "[x]",
    "skipped": "[-]",
    "blocked": "[!]",
}


def _percent(done, total):
    return int(round(done * 100.0 / total)) if total else 0


def _apply_status_timestamps(task, status):
    """Update started_at / completed_at to match a new status."""
    now = cf.now_iso()
    if status == "in_progress":
        task["started_at"] = task.get("started_at") or now
        task["completed_at"] = None
    elif status == "completed":
        task["started_at"] = task.get("started_at") or now
        task["completed_at"] = now
    elif status == "skipped":
        task["completed_at"] = now
    elif status == "pending":
        task["started_at"] = None
        task["completed_at"] = None
    # "blocked" leaves timestamps untouched.


def _refresh(state):
    """Recompute progress + overall status and bump the updated timestamp."""
    tasks = state.get("tasks", [])
    state["progress"] = cf.recompute_progress(tasks)
    state["status"] = cf.overall_status(tasks)
    state["updated"] = cf.now_iso()


def cmd_show(args):
    state = cf.read_json(args.state)
    tasks = state.get("tasks", [])
    progress = cf.recompute_progress(tasks)
    completed = progress["completed"]
    total = progress["total_tasks"]
    status = cf.overall_status(tasks)
    order = state.get("execution_order") or [t.get("id") for t in tasks]

    if args.json:
        print(json.dumps({
            "feature": state.get("feature"),
            "status": status,
            "progress": progress,
            "execution_order": order,
            "next": (cf.next_runnable_task(state) or {}).get("id"),
        }, indent=2, ensure_ascii=False))
        return 0

    print(f"feature: {state.get('feature')}   status: {status}   "
          f"progress: {completed}/{total} ({_percent(completed, total)}%)")
    if order:
        print("order: " + " > ".join(order))
    by_id = {t.get("id"): t for t in tasks}
    width = max((len(str(t)) for t in order), default=0)
    for tid in order:
        task = by_id.get(tid, {})
        icon = _STATUS_ICON.get(task.get("status", "pending"), "[ ]")
        pending_deps = [d for d in task.get("dependencies", [])
                        if by_id.get(d, {}).get("status") not in cf.DONE_STATUSES]
        dep_note = f"   (waiting on: {', '.join(pending_deps)})" if pending_deps else ""
        print(f"  {icon} {tid.ljust(width)}  {task.get('status', 'pending')}{dep_note}")
    return 0


def cmd_next(args):
    state = cf.read_json(args.state)
    task = cf.next_runnable_task(state)
    if task is None:
        print("ALL_DONE")
        return 0
    print(f"{task['id']}\t{task.get('title', '')}")
    return 0


def cmd_set_status(args):
    if args.status not in cf.TASK_STATUSES:
        sys.stderr.write(f"error: status must be one of {'|'.join(cf.TASK_STATUSES)}\n")
        return 2
    state = cf.read_json(args.state)
    task = next((t for t in state.get("tasks", []) if t.get("id") == args.task), None)
    if task is None:
        sys.stderr.write(f"error: task '{args.task}' not found in {args.state}\n")
        return 1
    task["status"] = args.status
    _apply_status_timestamps(task, args.status)
    _refresh(state)
    cf.write_json(args.state, state)
    p = state["progress"]
    print(f"{args.task} -> {args.status}   "
          f"({p['completed']}/{p['total_tasks']} done, status={state['status']})")
    return 0


def cmd_recompute(args):
    state = cf.read_json(args.state)
    _refresh(state)
    cf.write_json(args.state, state)
    p = state["progress"]
    print(f"recomputed: {p['completed']}/{p['total_tasks']} done, status={state['status']}")
    return 0


def cmd_init(args):
    raw = sys.stdin.read().strip()
    if not raw:
        sys.stderr.write("error: init expects a JSON array of tasks on stdin\n")
        return 2
    try:
        incoming = json.loads(raw)
    except ValueError as exc:
        sys.stderr.write(f"error: invalid JSON on stdin: {exc}\n")
        return 2
    if not isinstance(incoming, list) or not incoming:
        sys.stderr.write("error: stdin must be a non-empty JSON array of task objects\n")
        return 2

    tasks = []
    for entry in incoming:
        tid = entry.get("id")
        if not tid:
            sys.stderr.write("error: every task needs an 'id'\n")
            return 2
        tasks.append({
            "id": tid,
            "file": entry.get("file", f"tasks/{tid}.md"),
            "title": entry.get("title", tid),
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "assignee": None,
            "commits": [],
            "estimated_hours": entry.get("estimated_hours"),
            "dependencies": entry.get("dependencies", []),
        })

    try:
        order = cf.topo_order(tasks)
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1

    now = cf.now_iso()
    state = {
        "feature": args.feature,
        "created": now,
        "updated": now,
        "status": "pending",
        "execution_order": order,
        "progress": cf.recompute_progress(tasks),
        "tasks": tasks,
        "metadata": {
            "source_doc": args.source_doc,
            "created_by": args.created_by,
            "version": "1.0",
        },
    }

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        cf.write_json(args.output, state)
        print(f"wrote {args.output}  ({len(tasks)} tasks)")
    else:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_show = sub.add_parser("show", help="Compact summary + recomputed progress")
    p_show.add_argument("state")
    p_show.add_argument("--json", action="store_true", help="Machine-readable summary")
    p_show.set_defaults(func=cmd_show)

    p_next = sub.add_parser("next", help="Next runnable pending task")
    p_next.add_argument("state")
    p_next.set_defaults(func=cmd_next)

    p_set = sub.add_parser("set-status", help="Set a task status")
    p_set.add_argument("state")
    p_set.add_argument("task")
    p_set.add_argument("status")
    p_set.set_defaults(func=cmd_set_status)

    p_rec = sub.add_parser("recompute", help="Recompute progress + overall status")
    p_rec.add_argument("state")
    p_rec.set_defaults(func=cmd_recompute)

    p_init = sub.add_parser("init", help="Scaffold a new state.json (tasks via stdin)")
    p_init.add_argument("--feature", required=True)
    p_init.add_argument("--source-doc", default=None)
    p_init.add_argument("--created-by", default="code-forge")
    p_init.add_argument("--output", default=None, help="Write here (default: stdout)")
    p_init.set_defaults(func=cmd_init)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
