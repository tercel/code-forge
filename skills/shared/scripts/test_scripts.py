#!/usr/bin/env python3
"""Tests for the code-forge script layer. Standard-library unittest only.

Run: python3 skills/shared/scripts/test_scripts.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cf_common as cf  # noqa: E402

PY = sys.executable
CONFIG = os.path.join(HERE, "cf-config.py")
STATE = os.path.join(HERE, "cf-state.py")
STATUS = os.path.join(HERE, "cf-status.py")
VERIFY = os.path.join(HERE, "cf-verify-plan.py")
SCAN = os.path.join(HERE, "cf-scan.py")


def run(cmd, stdin=None):
    return subprocess.run(cmd, capture_output=True, text=True, input=stdin)


class CommonTests(unittest.TestCase):
    def test_deep_merge_nested(self):
        base = {"a": {"x": 1, "y": 2}, "b": 1}
        override = {"a": {"y": 9, "z": 3}}
        self.assertEqual(cf.deep_merge(base, override), {"a": {"x": 1, "y": 9, "z": 3}, "b": 1})

    def test_deep_merge_does_not_mutate_base(self):
        base = {"a": {"x": 1}}
        cf.deep_merge(base, {"a": {"x": 2}})
        self.assertEqual(base, {"a": {"x": 1}})

    def test_validate_rejects_traversal_and_absolute(self):
        errs = cf.validate_config({"directories": {"base": "", "input": "../x", "output": "/abs"}})
        self.assertTrue(any("input" in e and ".." in e for e in errs))
        self.assertTrue(any("output" in e for e in errs))

    def test_validate_rejects_source_base_and_bad_enum_and_string_bool(self):
        cfg = {"directories": {"base": "src/foo"}, "execution": {"default_mode": "yolo"},
               "git": {"commit_state_file": "true"}}
        errs = cf.validate_config(cfg)
        self.assertTrue(any("system/source" in e for e in errs))
        self.assertTrue(any("default_mode" in e for e in errs))
        self.assertTrue(any("commit_state_file" in e for e in errs))

    def test_validate_accepts_clean_config(self):
        self.assertEqual(cf.validate_config(cf.copy_defaults()), [])

    def test_resolve_dirs_default_and_tmp(self):
        cfg = cf.copy_defaults()
        base, inp, out = cf.resolve_dirs("/proj", cfg)
        self.assertEqual(base, os.path.normpath("/proj"))
        self.assertEqual(inp, os.path.normpath("/proj/docs/features"))
        self.assertEqual(out, os.path.normpath("/proj/planning"))
        _, _, tout = cf.resolve_dirs("/proj", cfg, tmp=True)
        self.assertEqual(tout, os.path.normpath("/proj/.code-forge/tmp"))

    def test_recompute_progress(self):
        tasks = [{"status": "completed"}, {"status": "completed"}, {"status": "in_progress"},
                 {"status": "pending"}, {"status": "skipped"}]
        p = cf.recompute_progress(tasks)
        self.assertEqual((p["total_tasks"], p["completed"], p["in_progress"], p["pending"], p["skipped"]),
                         (5, 2, 1, 1, 1))

    def test_overall_status(self):
        self.assertEqual(cf.overall_status([]), "pending")
        self.assertEqual(cf.overall_status([{"status": "pending"}]), "pending")
        self.assertEqual(cf.overall_status([{"status": "completed"}, {"status": "pending"}]), "in_progress")
        self.assertEqual(cf.overall_status([{"status": "completed"}, {"status": "skipped"}]), "completed")

    def test_topo_order_reorders_by_dependency(self):
        tasks = [{"id": "api", "dependencies": ["auth"]},
                 {"id": "auth", "dependencies": ["setup"]},
                 {"id": "setup", "dependencies": []}]
        self.assertEqual(cf.topo_order(tasks), ["setup", "auth", "api"])

    def test_topo_order_detects_cycle(self):
        with self.assertRaises(ValueError):
            cf.topo_order([{"id": "a", "dependencies": ["b"]}, {"id": "b", "dependencies": ["a"]}])

    def test_next_runnable_respects_deps(self):
        state = {"execution_order": ["a", "b"],
                 "tasks": [{"id": "a", "status": "pending", "dependencies": []},
                           {"id": "b", "status": "pending", "dependencies": ["a"]}]}
        first = cf.next_runnable_task(state)
        assert first is not None
        self.assertEqual(first["id"], "a")
        state["tasks"][0]["status"] = "completed"
        second = cf.next_runnable_task(state)
        assert second is not None
        self.assertEqual(second["id"], "b")
        state["tasks"][1]["status"] = "completed"
        self.assertIsNone(cf.next_runnable_task(state))


class ConfigCliTests(unittest.TestCase):
    def test_three_layer_merge_and_readonly_tool(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as home:
            with open(os.path.join(root, ".code-forge.json"), "w") as f:
                json.dump({"directories": {"output": "plans/"}, "_tool": {"name": "hacked"}}, f)
            with open(os.path.join(home, ".code-forge.json"), "w") as f:
                json.dump({"directories": {"input": "specs/"}}, f)
            res = run([PY, CONFIG, "--root", root, "--home", home])
            self.assertEqual(res.returncode, 0, res.stderr)
            out = json.loads(res.stdout)
            self.assertEqual(out["config"]["directories"]["output"], "plans/")
            self.assertEqual(out["config"]["directories"]["input"], "specs/")
            self.assertEqual(out["config"]["_tool"]["name"], "code-forge")  # read-only restored
            self.assertEqual(out["errors"], [])

    def test_invalid_config_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, ".code-forge.json"), "w") as f:
                json.dump({"directories": {"output": "../escape"}}, f)
            out = json.loads(run([PY, CONFIG, "--root", root]).stdout)
            self.assertTrue(out["errors"])
            self.assertEqual(out["config"]["directories"]["output"], "planning/")


class StateCliTests(unittest.TestCase):
    def _fresh_state(self, root):
        d = os.path.join(root, "planning", "feat")
        os.makedirs(d)
        path = os.path.join(d, "state.json")
        tasks = '[{"id":"setup","title":"S","dependencies":[]},{"id":"api","title":"A","dependencies":["setup"]}]'
        run([PY, STATE, "init", "--feature", "feat", "--output", path], stdin=tasks)
        return path

    def test_init_topo_and_progress(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._fresh_state(root)
            state = cf.read_json(path)
            self.assertEqual(state["execution_order"], ["setup", "api"])
            self.assertEqual(state["progress"]["total_tasks"], 2)
            self.assertEqual(state["status"], "pending")

    def test_set_status_timestamps_and_progress(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._fresh_state(root)
            run([PY, STATE, "set-status", path, "setup", "completed"])
            state = cf.read_json(path)
            setup = next(t for t in state["tasks"] if t["id"] == "setup")
            self.assertIsNotNone(setup["completed_at"])
            self.assertIsNotNone(setup["started_at"])
            self.assertEqual(state["progress"]["completed"], 1)
            self.assertEqual(state["status"], "in_progress")

    def test_next_advances(self):
        with tempfile.TemporaryDirectory() as root:
            path = self._fresh_state(root)
            self.assertEqual(run([PY, STATE, "next", path]).stdout.split("\t")[0], "setup")
            run([PY, STATE, "set-status", path, "setup", "completed"])
            self.assertEqual(run([PY, STATE, "next", path]).stdout.split("\t")[0], "api")
            run([PY, STATE, "set-status", path, "api", "completed"])
            self.assertEqual(run([PY, STATE, "next", path]).stdout.strip(), "ALL_DONE")

    def test_init_cycle_errors(self):
        res = run([PY, STATE, "init", "--feature", "c"],
                  stdin='[{"id":"a","dependencies":["b"]},{"id":"b","dependencies":["a"]}]')
        self.assertNotEqual(res.returncode, 0)


class StatusCliTests(unittest.TestCase):
    def test_dashboard_and_detail(self):
        with tempfile.TemporaryDirectory() as root:
            open(os.path.join(root, ".git"), "w").close()
            d = os.path.join(root, "planning", "feat")
            os.makedirs(d)
            path = os.path.join(d, "state.json")
            run([PY, STATE, "init", "--feature", "feat", "--output", path],
                stdin='[{"id":"setup","title":"S","dependencies":[]}]')
            run([PY, STATE, "set-status", path, "setup", "completed"])

            dash = run([PY, STATUS, "--root", root])
            self.assertEqual(dash.returncode, 0, dash.stderr)
            self.assertIn("feat", dash.stdout)
            self.assertIn("1/1 (100%)", dash.stdout)

            detail = run([PY, STATUS, "--root", root, "feat"])
            self.assertIn("Feature: feat", detail.stdout)
            self.assertIn("completed", detail.stdout)

            missing = run([PY, STATUS, "--root", root, "nope"])
            self.assertNotEqual(missing.returncode, 0)


def _build_valid_plan(root):
    """Create a structurally complete feature plan directory and return its path."""
    feat = os.path.join(root, "planning", "feat")
    os.makedirs(os.path.join(feat, "tasks"))
    run([PY, STATE, "init", "--feature", "feat", "--output", os.path.join(feat, "state.json")],
        stdin='[{"id":"setup","title":"S","dependencies":[]},'
              '{"id":"api","title":"A","dependencies":["setup"]}]')
    with open(os.path.join(feat, "plan.md"), "w") as f:
        f.write("# Feat\n\n## Goal\nx\n\n## Task Breakdown\nx\n\n## Acceptance Criteria\nx\n")
    with open(os.path.join(feat, "overview.md"), "w") as f:
        f.write("# Feat\n\n## Task Execution Order\nx\n")
    for tid in ("setup", "api"):
        with open(os.path.join(feat, "tasks", f"{tid}.md"), "w") as f:
            f.write(f"# {tid}\n")
    return feat


class VerifyPlanTests(unittest.TestCase):
    def test_valid_plan_passes(self):
        with tempfile.TemporaryDirectory() as root:
            feat = _build_valid_plan(root)
            res = run([PY, VERIFY, feat])
            self.assertEqual(res.returncode, 0, res.stdout)

    def test_broken_execution_order_and_missing_task_file(self):
        with tempfile.TemporaryDirectory() as root:
            feat = _build_valid_plan(root)
            os.remove(os.path.join(feat, "tasks", "api.md"))
            state_path = os.path.join(feat, "state.json")
            state = cf.read_json(state_path)
            state["execution_order"].append("ghost")
            cf.write_json(state_path, state)
            res = run([PY, VERIFY, feat, "--json"])
            self.assertEqual(res.returncode, 1)
            errors = json.loads(res.stdout)["errors"]
            self.assertTrue(any("execution_order" in e for e in errors))
            self.assertTrue(any("api.md" in e for e in errors))

    def test_strict_promotes_missing_sections(self):
        with tempfile.TemporaryDirectory() as root:
            feat = _build_valid_plan(root)
            with open(os.path.join(feat, "plan.md"), "w") as f:
                f.write("just text, no headings\n")
            self.assertEqual(run([PY, VERIFY, feat]).returncode, 0)         # warnings only
            self.assertEqual(run([PY, VERIFY, feat, "--strict"]).returncode, 1)  # promoted


class ScanTests(unittest.TestCase):
    def test_detects_language_framework_test_and_signals(self):
        with tempfile.TemporaryDirectory() as root:
            open(os.path.join(root, ".git"), "w").close()
            os.makedirs(os.path.join(root, "src", "app"))
            os.makedirs(os.path.join(root, "tests"))
            os.makedirs(os.path.join(root, "alembic"))
            with open(os.path.join(root, "pyproject.toml"), "w") as f:
                f.write('[project]\nname="d"\ndependencies=["fastapi","sqlalchemy","pyjwt"]\n')
            with open(os.path.join(root, "requirements.txt"), "w") as f:
                f.write("pytest\n")
            for p in ("src/app/main.py", "tests/test_main.py", "main.py"):
                open(os.path.join(root, p), "w").close()

            out = json.loads(run([PY, SCAN, "--root", root]).stdout)
            self.assertEqual(out["primary_language"], "Python")
            self.assertIn("FastAPI", out["frameworks"])
            self.assertEqual(out["test"]["framework"], "pytest")
            self.assertEqual(out["test"]["command"], "pytest")
            self.assertTrue(out["signals"]["database"])
            self.assertTrue(out["signals"]["auth"])
            self.assertIn("main.py", out["entrypoints"])

    def test_empty_project_does_not_crash(self):
        with tempfile.TemporaryDirectory() as root:
            open(os.path.join(root, ".git"), "w").close()
            out = json.loads(run([PY, SCAN, "--root", root]).stdout)
            self.assertIsNone(out["primary_language"])
            self.assertEqual(out["frameworks"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
