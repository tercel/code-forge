"""Shared helpers for the code-forge script layer.

Used by cf-config.py, cf-state.py, and cf-status.py. Pure Python 3 standard
library only — no third-party dependencies, no pip installs. Sibling scripts
import this module directly because they live in the same directory.
"""

import json
import os
from datetime import datetime, timezone

# Project-root markers, highest-priority first. The walk stops at the first
# directory containing any of these.
ROOT_MARKERS = [
    ".code-forge.json",
    ".git",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "build.gradle",
    "pom.xml",
    "Makefile",
]

# Layer 1 of the config merge. _tool is read-only and is always forced back to
# these values after merging (callers must not override it).
SYSTEM_DEFAULTS = {
    "_tool": {
        "name": "code-forge",
        "description": "Transform documentation into actionable development plans with task breakdown and status tracking",
        "url": "https://github.com/tercel/code-forge",
    },
    "directories": {"base": "", "input": "docs/features/", "output": "planning/"},
    "git": {"auto_commit": False, "commit_state_file": True, "gitignore_patterns": []},
    "execution": {"default_mode": "ask", "auto_tdd": True, "task_granularity": "medium"},
}

TASK_STATUSES = ["pending", "in_progress", "completed", "skipped", "blocked"]
# Statuses that count as "no longer blocking downstream work".
DONE_STATUSES = {"completed", "skipped"}


def now_iso():
    """Return the current UTC time as an ISO-8601 string (e.g. 2026-06-10T12:00:00Z)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, data):
    """Write JSON with stable 2-space indentation and a trailing newline."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def copy_defaults():
    """Return a deep copy of SYSTEM_DEFAULTS so callers never mutate the template."""
    return json.loads(json.dumps(SYSTEM_DEFAULTS))


def find_project_root(start=None):
    """Walk upward from `start` (or cwd) until a ROOT_MARKER is found.

    Falls back to the starting directory if no marker exists anywhere above.
    """
    start_abs = os.path.abspath(start or os.getcwd())
    cur = start_abs
    while True:
        for marker in ROOT_MARKERS:
            if os.path.exists(os.path.join(cur, marker)):
                return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return start_abs
        cur = parent


def deep_merge(base, override):
    """Recursively merge `override` into `base`, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(root, home=None):
    """Load the three-layer merged config.

    Returns (config, sources, load_errors). load_errors holds messages for
    config files that exist but could not be parsed.
    """
    sources = ["system defaults"]
    config = copy_defaults()
    load_errors = []

    home = home or os.path.expanduser("~")
    user_path = os.path.join(home, ".code-forge.json")
    project_path = os.path.join(root, ".code-forge.json")

    for path, label in (
        (user_path, "user config (~/.code-forge.json)"),
        (project_path, "project config (.code-forge.json)"),
    ):
        if os.path.isfile(path):
            try:
                config = deep_merge(config, read_json(path))
                sources.append(label)
            except (OSError, ValueError) as exc:
                load_errors.append(f"Failed to read {path}: {exc}")

    # _tool is read-only — restore it regardless of what the layers contained.
    config["_tool"] = copy_defaults()["_tool"]
    return config, sources, load_errors


def validate_config(config):
    """Return a list of validation error strings (empty when valid)."""
    errors = []
    dirs = config.get("directories", {})

    for key in ("base", "input", "output"):
        val = dirs.get(key, "") or ""
        if ".." in val:
            errors.append(f"directories.{key} must not contain '..' (path traversal risk)")
        if val.startswith("/"):
            errors.append(f"directories.{key} must be a relative path (must not start with '/')")

    base = (dirs.get("base", "") or "").strip("/")
    base_head = base.split("/")[0] if base else ""
    if base_head in {"src", "node_modules", "build", ".git"}:
        errors.append(f"directories.base must not be a system/source directory ('{base_head}')")

    git = config.get("git", {})
    if "commit_state_file" in git and not isinstance(git["commit_state_file"], bool):
        errors.append("git.commit_state_file must be a boolean (not a string)")

    mode = config.get("execution", {}).get("default_mode")
    if mode is not None and mode not in ("ask", "manual", "auto"):
        errors.append(f"execution.default_mode must be one of ask|manual|auto (got '{mode}')")

    return errors


def resolve_dirs(root, config, tmp=False):
    """Resolve base/input/output absolute directories from the merged config."""
    dirs = config.get("directories", {})
    base_dir = os.path.normpath(os.path.join(root, dirs.get("base", "") or ""))
    input_dir = os.path.normpath(os.path.join(base_dir, dirs.get("input", "") or ""))
    if tmp:
        output_dir = os.path.normpath(os.path.join(root, ".code-forge", "tmp"))
    else:
        output_dir = os.path.normpath(os.path.join(base_dir, dirs.get("output", "") or ""))
    return base_dir, input_dir, output_dir


def recompute_progress(tasks):
    """Recompute the progress block from the task list."""
    counts = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        status = task.get("status", "pending")
        counts[status] = counts.get(status, 0) + 1
    return {
        "total_tasks": len(tasks),
        "completed": counts["completed"],
        "in_progress": counts["in_progress"],
        "pending": counts["pending"],
        "skipped": counts["skipped"],
        "blocked": counts["blocked"],
    }


def overall_status(tasks):
    """Derive the feature-level status from its tasks."""
    total = len(tasks)
    if total == 0:
        return "pending"
    done = sum(1 for t in tasks if t.get("status") in DONE_STATUSES)
    if done == total:
        return "completed"
    active = any(
        t.get("status") in ("in_progress", "completed", "skipped", "blocked") for t in tasks
    )
    return "in_progress" if active else "pending"


def topo_order(tasks):
    """Return a dependency-respecting task-id order (Kahn's algorithm).

    Ties are broken by original input order for determinism. Raises ValueError
    on a dependency cycle.
    """
    ids = [t["id"] for t in tasks]
    index = {tid: i for i, tid in enumerate(ids)}
    id_set = set(ids)
    deps = {t["id"]: [d for d in t.get("dependencies", []) if d in id_set] for t in tasks}

    indegree = {tid: 0 for tid in ids}
    for tid in ids:
        indegree[tid] = len(deps[tid])

    available = sorted([tid for tid in ids if indegree[tid] == 0], key=lambda x: index[x])
    order = []
    while available:
        node = available.pop(0)
        order.append(node)
        for tid in ids:
            if node in deps[tid]:
                indegree[tid] -= 1
                if indegree[tid] == 0:
                    available.append(tid)
        available.sort(key=lambda x: index[x])

    if len(order) != len(ids):
        remaining = [tid for tid in ids if tid not in order]
        raise ValueError(f"Dependency cycle detected among tasks: {remaining}")
    return order


def next_runnable_task(state):
    """Return the next pending task whose dependencies are all done, or None."""
    tasks_by_id = {t["id"]: t for t in state.get("tasks", [])}
    order = state.get("execution_order") or list(tasks_by_id.keys())
    for tid in order:
        task = tasks_by_id.get(tid)
        if not task or task.get("status") != "pending":
            continue
        deps = task.get("dependencies", [])
        if all(tasks_by_id.get(d, {}).get("status") in DONE_STATUSES for d in deps):
            return task
    return None
