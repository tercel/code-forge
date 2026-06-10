#!/usr/bin/env python3
"""Verify the structural integrity of a code-forge feature plan directory.

Covers the checks in impl Step 4 and plan Step 12: required files exist and are
non-empty, state.json is valid and internally consistent (fields present,
execution_order <-> tasks IDs match, referenced task files exist), and the
markdown documents contain their required sections.

Severity:
  ERROR  structural problems (missing files, invalid/inconsistent state.json)
  WARN   content/cosmetic problems (missing sections, count mismatch, numeric
         task prefixes, missing project-level overview, legacy plan dirs)

--strict promotes every WARN to ERROR (use it for plan Step 12, which requires
all checks to pass). Exit code is non-zero when any ERROR remains.

Usage:
  cf-verify-plan.py <feature_dir> [--output-dir DIR] [--root PATH] [--strict] [--json]
"""

import argparse
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # never write .pyc into a possibly read-only install dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf_common as cf

REQUIRED_STATE_FIELDS = ["feature", "status", "execution_order", "progress", "tasks"]
PLAN_SECTIONS = ["Goal", "Task Breakdown", "Acceptance Criteria"]
OVERVIEW_SECTION = "Task Execution Order"
LEGACY_DIRS = ["docs/plan", "docs/plans", "docs/planning"]
NUMERIC_PREFIX = re.compile(r"^\d+[-_]")


class Report:
    def __init__(self):
        self.checks = []  # (severity, passed, message)

    def add(self, severity, passed, message):
        self.checks.append((severity, passed, message))

    def errors(self, strict):
        out = []
        for severity, passed, message in self.checks:
            if passed:
                continue
            if severity == "ERROR" or (strict and severity == "WARN"):
                out.append(message)
        return out

    def warnings(self, strict):
        if strict:
            return []
        return [m for sev, ok, m in self.checks if not ok and sev == "WARN"]


def _nonempty_file(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _has_heading(text, keyword):
    """True if a markdown heading line contains the keyword (case-insensitive)."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and keyword.lower() in stripped.lower():
            return True
    return False


def verify(feature_dir, output_dir=None, root=None):
    rep = Report()
    feature_dir = os.path.abspath(feature_dir)

    rep.add("ERROR", os.path.isdir(feature_dir), f"feature directory exists: {feature_dir}")

    overview = os.path.join(feature_dir, "overview.md")
    plan = os.path.join(feature_dir, "plan.md")
    state_path = os.path.join(feature_dir, "state.json")
    tasks_dir = os.path.join(feature_dir, "tasks")

    rep.add("ERROR", _nonempty_file(overview), "overview.md exists and is non-empty")
    rep.add("ERROR", _nonempty_file(plan), "plan.md exists and is non-empty")
    rep.add("ERROR", _nonempty_file(state_path), "state.json exists and is non-empty")

    task_files = sorted(glob.glob(os.path.join(tasks_dir, "*.md")))
    rep.add("ERROR", os.path.isdir(tasks_dir), "tasks/ directory exists")
    rep.add("ERROR", len(task_files) > 0, "tasks/ contains at least one .md file")

    numeric = [os.path.basename(p) for p in task_files if NUMERIC_PREFIX.match(os.path.basename(p))]
    rep.add("WARN", not numeric,
            f"task files use descriptive names (no numeric prefixes){'; offenders: ' + ', '.join(numeric) if numeric else ''}")

    # state.json parsing + consistency
    state = None
    if _nonempty_file(state_path):
        try:
            state = cf.read_json(state_path)
            rep.add("ERROR", True, "state.json is valid JSON")
        except ValueError as exc:
            rep.add("ERROR", False, f"state.json is valid JSON ({exc})")

    if state is not None:
        missing = [f for f in REQUIRED_STATE_FIELDS if f not in state]
        rep.add("ERROR", not missing,
                f"state.json has required fields{'; missing: ' + ', '.join(missing) if missing else ''}")

        tasks = state.get("tasks", []) if isinstance(state.get("tasks"), list) else []
        order = state.get("execution_order", []) if isinstance(state.get("execution_order"), list) else []
        task_ids = {t.get("id") for t in tasks}

        order_extra = [tid for tid in order if tid not in task_ids]
        order_missing = [tid for tid in task_ids if tid not in order]
        consistent = not order_extra and not order_missing
        detail = ""
        if order_extra:
            detail += f"; in execution_order but not tasks: {', '.join(map(str, order_extra))}"
        if order_missing:
            detail += f"; in tasks but not execution_order: {', '.join(map(str, order_missing))}"
        rep.add("ERROR", consistent, f"execution_order matches tasks entries{detail}")

        # every referenced task file exists
        bad_refs = []
        for t in tasks:
            ref = t.get("file")
            if ref and not os.path.isfile(os.path.join(feature_dir, ref)):
                bad_refs.append(ref)
        rep.add("ERROR", not bad_refs,
                f"every task 'file' exists on disk{'; missing: ' + ', '.join(bad_refs) if bad_refs else ''}")

        # task count vs files (warning)
        rep.add("WARN", len(tasks) == len(task_files),
                f"task count matches files ({len(tasks)} tasks / {len(task_files)} files)")

    # markdown sections (warnings)
    plan_text = _read_text(plan)
    rep.add("WARN", _has_heading(plan_text, "#") or bool(re.search(r"(?m)^#\s", plan_text)),
            "plan.md has a title heading")
    for section in PLAN_SECTIONS:
        rep.add("WARN", _has_heading(plan_text, section), f"plan.md has section: ## {section}")

    overview_text = _read_text(overview)
    rep.add("WARN", _has_heading(overview_text, OVERVIEW_SECTION),
            f"overview.md has section: ## {OVERVIEW_SECTION}")

    # project-level overview (warning, only when output_dir known)
    if output_dir:
        proj_overview = os.path.join(output_dir, "overview.md")
        rep.add("WARN", _nonempty_file(proj_overview),
                f"project-level overview exists: {proj_overview}")

    # legacy plan dirs (warning, only when root known)
    if root:
        present = [d for d in LEGACY_DIRS if os.path.isdir(os.path.join(root, d))]
        rep.add("WARN", not present,
                f"no legacy plan directories{'; found: ' + ', '.join(present) if present else ''}")

    return rep


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("feature_dir", help="Path to the feature plan directory")
    parser.add_argument("--output-dir", help="Output dir (enables project-overview check)")
    parser.add_argument("--root", help="Project root (enables legacy-dir check)")
    parser.add_argument("--strict", action="store_true", help="Promote warnings to errors")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    rep = verify(args.feature_dir, output_dir=args.output_dir, root=args.root)
    errors = rep.errors(args.strict)
    warnings = rep.warnings(args.strict)

    if args.json:
        print(json.dumps({
            "errors": errors,
            "warnings": warnings,
            "checks": [{"severity": s, "passed": p, "message": m} for s, p, m in rep.checks],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Plan verification: {os.path.abspath(args.feature_dir)}")
        for severity, passed, message in rep.checks:
            if passed:
                tag = "PASS"
            elif severity == "ERROR" or (args.strict and severity == "WARN"):
                tag = "FAIL"
            else:
                tag = "WARN"
            print(f"  [{tag}] {message}")
        print(f"Result: {len(errors)} error(s), {len(warnings)} warning(s)")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
