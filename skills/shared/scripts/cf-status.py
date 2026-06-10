#!/usr/bin/env python3
"""Render the code-forge status dashboard or a single feature detail.

Scans for state.json files and prints a ready-to-display table, so the raw
state files never need to enter the model's context.

Usage:
  cf-status.py [--root PATH] [--output-dir DIR]            Project dashboard
  cf-status.py [--root PATH] [--output-dir DIR] <feature>  Feature detail
  add --json for machine-readable output.

When --output-dir is omitted it is resolved the same way cf-config.py does
(detect root, merge config, apply directories.output).
"""

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_common as cf


def _percent(done, total):
    return int(round(done * 100.0 / total)) if total else 0


def _date(value):
    """Trim an ISO timestamp to its date portion for display."""
    if not value:
        return "—"
    return str(value).split("T")[0]


def _render_table(headers, rows):
    """Render a simple fixed-width text table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    lines = ["  " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))]
    for row in rows:
        lines.append("  " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
    return "\n".join(lines)


def _collect_features(output_dir, tmp_dir):
    """Return a list of feature summaries from all discovered state.json files."""
    features = []
    seen = set()
    for base, is_tmp in ((output_dir, False), (tmp_dir, True)):
        if not base or not os.path.isdir(base):
            continue
        for state_path in sorted(glob.glob(os.path.join(base, "*", "state.json"))):
            try:
                state = cf.read_json(state_path)
            except (OSError, ValueError):
                continue
            name = state.get("feature") or os.path.basename(os.path.dirname(state_path))
            key = (name, is_tmp)
            if key in seen:
                continue
            seen.add(key)
            tasks = state.get("tasks", [])
            progress = cf.recompute_progress(tasks)
            features.append({
                "feature": name,
                "tmp": is_tmp,
                "completed": progress["completed"],
                "total": progress["total_tasks"],
                "status": cf.overall_status(tasks),
                "updated": state.get("updated"),
                "source_doc": state.get("metadata", {}).get("source_doc"),
                "path": state_path,
            })
    return features


def cmd_dashboard(output_dir, tmp_dir, as_json):
    features = _collect_features(output_dir, tmp_dir)

    if as_json:
        print(json.dumps(features, indent=2, ensure_ascii=False))
        return 0

    if not features:
        print("code-forge — Feature Dashboard\n")
        print("No features found.\n")
        print("Create one with:")
        print("  /code-forge:plan @path/to/feature.md     Plan from a document")
        print('  /code-forge:plan "requirement text"      Plan from a prompt')
        return 0

    rows = []
    for i, f in enumerate(features, 1):
        label = f["feature"] + (" [tmp]" if f["tmp"] else "")
        progress = f"{f['completed']}/{f['total']} ({_percent(f['completed'], f['total'])}%)"
        rows.append([i, label, progress, f["status"], _date(f["updated"])])

    print("code-forge — Feature Dashboard\n")
    print(_render_table(["#", "Feature", "Progress", "Status", "Last Updated"], rows))
    print("\nCommands:")
    print("  /code-forge:plan @doc.md          Create new plan from document")
    print("  /code-forge:impl <feature>        Execute tasks for a feature")
    print("  /code-forge:status <feature>      View feature detail")
    print("  /code-forge:review <feature>      Review completed feature")
    return 0


def _find_feature_state(feature, output_dir, tmp_dir):
    candidates = [
        os.path.join(output_dir, feature, "state.json"),
        os.path.join(tmp_dir, feature, "state.json"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def cmd_detail(feature, output_dir, tmp_dir, as_json):
    path = _find_feature_state(feature, output_dir, tmp_dir)
    if path is None:
        sys.stderr.write(f"error: feature '{feature}' not found. "
                         f"Run /code-forge:status to list features.\n")
        return 1
    state = cf.read_json(path)
    tasks = state.get("tasks", [])
    order = state.get("execution_order") or [t.get("id") for t in tasks]
    by_id = {t.get("id"): t for t in tasks}
    progress = cf.recompute_progress(tasks)

    if as_json:
        print(json.dumps({
            "feature": state.get("feature"),
            "status": cf.overall_status(tasks),
            "progress": progress,
            "path": path,
        }, indent=2, ensure_ascii=False))
        return 0

    print(f"code-forge — Feature: {state.get('feature')}\n")
    print(f"Status: {cf.overall_status(tasks)}")
    print(f"Source: {state.get('metadata', {}).get('source_doc') or '—'}")
    print(f"Created: {_date(state.get('created'))}")
    print(f"Updated: {_date(state.get('updated'))}\n")

    rows = []
    for i, tid in enumerate(order, 1):
        task = by_id.get(tid, {})
        rows.append([
            i,
            tid,
            task.get("status", "pending"),
            _date(task.get("started_at")),
            _date(task.get("completed_at")),
        ])
    print("Tasks:")
    print(_render_table(["#", "Task", "Status", "Started", "Completed"], rows))
    print(f"\nProgress: {progress['completed']}/{progress['total_tasks']} "
          f"({_percent(progress['completed'], progress['total_tasks'])}%)")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("feature", nargs="?", help="Feature name for detail view")
    parser.add_argument("--root", help="Project root (default: auto-detect)")
    parser.add_argument("--output-dir", help="Output directory (default: resolved from config)")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    root = os.path.abspath(args.root) if args.root else cf.find_project_root()
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
    else:
        config, _, _ = cf.load_config(root)
        _, _, output_dir = cf.resolve_dirs(root, config)
    tmp_dir = os.path.join(root, ".code-forge", "tmp")

    if args.feature:
        return cmd_detail(args.feature, output_dir, tmp_dir, args.json)
    return cmd_dashboard(output_dir, tmp_dir, args.json)


if __name__ == "__main__":
    sys.exit(main())
