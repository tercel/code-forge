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
GROUP = os.path.join(HERE, "cf-group.py")


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


class HygieneTests(unittest.TestCase):
    CLIS = ["cf-config.py", "cf-state.py", "cf-status.py", "cf-verify-plan.py", "cf-scan.py",
            "cf-group.py"]

    def test_clis_disable_bytecode_writes(self):
        # Guards read-only installs and keeps the shared install dir clean.
        for name in self.CLIS:
            with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                self.assertIn("sys.dont_write_bytecode = True", fh.read(),
                              f"{name} must disable bytecode writes")

    def test_cli_run_writes_no_pycache(self):
        # Copy the layer to a temp dir and confirm a CLI run leaves no __pycache__.
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, "scripts")
            shutil.copytree(HERE, dst, ignore=shutil.ignore_patterns("__pycache__"))
            subprocess.run([PY, os.path.join(dst, "cf-config.py"), "--root", tmp],
                           capture_output=True, text=True)
            self.assertFalse(os.path.isdir(os.path.join(dst, "__pycache__")))


def group(scope):
    """Run cf-group.py over a scope dict and return the parsed partition."""
    r = run([PY, GROUP], stdin=json.dumps(scope))
    assert r.returncode in (0, 1), f"cf-group failed: {r.stderr}"
    return json.loads(r.stdout)


class GroupPartitionTests(unittest.TestCase):
    """Module grouping — review SKILL.md 3F.3.

    Several of these are regressions for failure modes that shipped in the
    prose rules: group count treated as files/cap, merging referenced but never
    defined, and thresholds left unstated.
    """

    def test_fragmented_directories_merge_below_cap(self):
        # 26 directories holding one file each. Group count is set by directory
        # count, NOT by files/cap — this is the case the prose rules missed.
        files = [f"src/m{i:02d}/f.ts" for i in range(26)]
        res = group({"files": files, "manifests": ["package.json"]})
        self.assertLessEqual(res["group_count"], 8)
        self.assertTrue(res["groups_merged"])
        self.assertFalse(res["guardrail"]["triggered"])

    def test_fragmented_scope_keeps_full_coverage(self):
        files = [f"src/m{i:02d}/f.ts" for i in range(26)]
        res = group({"files": files, "manifests": ["package.json"]})
        self.assertTrue(res["coverage_ok"])
        flat = sorted(f for g in res["groups"] for f in g["files"])
        self.assertEqual(flat, sorted(files))

    def test_count_cap_wins_over_size_cap(self):
        # Merging to satisfy the group cap may exceed the size cap. Count is
        # hard (agent fan-out); size only degrades per-agent context.
        # Note this can only arise once the scope is already past the guardrail
        # (files > cap * 8) — below that, merging never has to break the size
        # cap, which is what makes the two thresholds mutually consistent.
        files = [f"src/m{i:02d}/f.ts" for i in range(60)]
        res = group({"files": files, "manifests": ["package.json"]})
        self.assertLessEqual(res["group_count"], 8)
        self.assertGreater(res["largest_group"], res["size_cap"])
        self.assertTrue(res["guardrail"]["triggered"])

    def test_package_boundary_blocks_merge(self):
        # Nine independent packages cannot be merged into eight groups without
        # crossing a boundary, so the guardrail fires instead of merging.
        files = [f"packages/p{i}/src/f.ts" for i in range(9)]
        manifests = [f"packages/p{i}/package.json" for i in range(9)]
        res = group({"files": files, "manifests": manifests})
        self.assertEqual(res["group_count"], 9)
        self.assertTrue(res["guardrail"]["triggered"])
        self.assertIn("no mergeable pair remains", " ".join(res["guardrail"]["reasons"]))

    def test_merge_never_crosses_package_boundary(self):
        files = ([f"libs/backend/a{i}/f.ts" for i in range(6)]
                 + [f"libs/frontend/b{i}/f.ts" for i in range(6)])
        res = group({"files": files,
                     "manifests": ["libs/backend/package.json", "libs/frontend/package.json"]})
        for g in res["groups"]:
            roots = {f.split("/")[1] for f in g["files"]}
            self.assertEqual(len(roots), 1, f"group straddles packages: {g}")

    def test_barrel_is_transparent_and_not_a_node(self):
        scope = {
            "files": ["src/a/caller.ts", "src/index.ts", "src/b/target.ts"],
            "edges": [["src/a/caller.ts", "src/index.ts"],
                      ["src/index.ts", "src/b/target.ts"]],
            "barrels": ["src/index.ts"],
            "architecture_pattern": "Layered API",
        }
        res = group(scope)
        self.assertNotIn("src/index.ts", res["in_diff_files"])
        self.assertEqual(res["edge_count"], 1)  # collapsed to caller -> target

    def test_layered_scope_groups_by_chain(self):
        # Two end-to-end chains across three directories each. The axis must
        # follow the chains, so each agent sees a whole chain.
        scope = {
            "files": ["r/one.ts", "s/one.ts", "d/one.ts",
                      "r/two.ts", "s/two.ts", "d/two.ts"],
            "edges": [["r/one.ts", "s/one.ts"], ["s/one.ts", "d/one.ts"],
                      ["r/two.ts", "s/two.ts"], ["s/two.ts", "d/two.ts"]],
            "architecture_pattern": "Layered API",
        }
        res = group(scope)
        self.assertEqual(res["grouping_strategy"], "S2")
        for g in res["groups"]:
            suffixes = {f.split("/")[1] for f in g["files"]}
            self.assertEqual(len(suffixes), 1, f"chain was split: {g}")

    def test_low_cut_ratio_overrides_layered_pattern(self):
        # A layered project whose diff sits inside one layer has nothing to gain
        # from the chain axis — the measurement beats the pattern label.
        scope = {
            "files": ["s/a.ts", "s/b.ts", "s/c.ts"],
            "edges": [["s/a.ts", "s/b.ts"], ["s/b.ts", "s/c.ts"]],
            "architecture_pattern": "Layered API",
        }
        self.assertEqual(group(scope)["grouping_strategy"], "S1")

    def test_plugin_pattern_uses_directory_axis(self):
        scope = {
            "files": ["plugins/a/i.ts", "plugins/a/j.ts",
                      "plugins/b/i.ts", "plugins/b/j.ts"],
            "edges": [["plugins/a/i.ts", "plugins/a/j.ts"],
                      ["plugins/b/i.ts", "plugins/b/j.ts"]],
            "architecture_pattern": "Plugin/Extension",
        }
        res = group(scope)
        self.assertEqual(res["grouping_strategy"], "S1")
        self.assertEqual(res["cut_ratio"], 0.0)

    def test_isolated_file_does_not_become_its_own_group(self):
        # A zero-edge file has no "most edges to" target; it must still attach.
        scope = {
            "files": ["r/a.ts", "s/a.ts", "d/a.ts", "r/b.ts", "s/b.ts", "d/b.ts",
                      "r/orphan.ts"],
            "edges": [["r/a.ts", "s/a.ts"], ["s/a.ts", "d/a.ts"],
                      ["r/b.ts", "s/b.ts"], ["s/b.ts", "d/b.ts"]],
            "architecture_pattern": "Layered API",
        }
        res = group(scope)
        self.assertEqual(res["grouping_strategy"], "S2")
        for g in res["groups"]:
            if g["files"] == ["r/orphan.ts"]:
                self.fail("orphan file became its own group")
        self.assertTrue(res["coverage_ok"])

    def test_orphan_does_not_cross_package_boundary(self):
        # Caught end-to-end, not by the earlier unit tests: a zero-edge file was
        # attached by path prefix alone and landed in another package's agent.
        scope = {
            "files": ["apps/api/r/a.ts", "apps/api/s/a.ts", "apps/api/d/a.ts",
                      "apps/api/r/b.ts", "apps/api/s/b.ts", "apps/api/d/b.ts",
                      "apps/web/components/x.tsx"],
            "edges": [["apps/api/r/a.ts", "apps/api/s/a.ts"],
                      ["apps/api/s/a.ts", "apps/api/d/a.ts"],
                      ["apps/api/r/b.ts", "apps/api/s/b.ts"],
                      ["apps/api/s/b.ts", "apps/api/d/b.ts"]],
            "manifests": ["apps/api/package.json", "apps/web/package.json"],
            "architecture_pattern": "Layered API",
        }
        res = group(scope)
        for g in res["groups"]:
            pkgs = {f.split("/")[1] for f in g["files"]}
            self.assertEqual(len(pkgs), 1, f"group straddles packages: {g}")
        self.assertTrue(res["coverage_ok"])

    def test_edge_bearing_file_may_cross_package_boundary(self):
        # The asymmetry: a real import edge is evidence, so a genuine
        # cross-package chain stays whole. Only path-guessing is constrained.
        scope = {
            "files": ["apps/api/r/a.ts", "libs/core/s/a.ts", "libs/core/d/a.ts"],
            "edges": [["apps/api/r/a.ts", "libs/core/s/a.ts"],
                      ["libs/core/s/a.ts", "libs/core/d/a.ts"]],
            "manifests": ["apps/api/package.json", "libs/core/package.json"],
            "architecture_pattern": "Layered API",
        }
        res = group(scope)
        self.assertEqual(res["group_count"], 1)
        self.assertEqual(len(res["groups"][0]["files"]), 3)

    def test_dense_blob_is_not_split(self):
        scope = {
            "files": [f"src/f{i}.ts" for i in range(8)],
            "edges": [[f"src/f{i}.ts", f"src/f{i + 1}.ts"] for i in range(7)],
            "architecture_pattern": "Layered API",
        }
        res = group(scope)
        self.assertEqual(res["grouping_strategy"], "S3")
        self.assertEqual(res["group_count"], 1)
        self.assertEqual(res["path"], "fast")

    def test_dense_blob_above_single_agent_limit_is_blocked(self):
        # S3 has no safe execution above 12 files: do not split it anyway.
        scope = {
            "files": [f"src/f{i:02d}.ts" for i in range(20)],
            "edges": [[f"src/f{i:02d}.ts", f"src/f{i + 1:02d}.ts"] for i in range(19)],
            "architecture_pattern": "Layered API",
        }
        res = group(scope)
        self.assertEqual(res["grouping_strategy"], "S3")
        self.assertEqual(res["path"], "blocked")
        self.assertTrue(res["guardrail"]["triggered"])

    def test_scope_guardrail_fires_above_48_files(self):
        files = [f"src/m{i % 6}/f{i:02d}.ts" for i in range(60)]
        res = group({"files": files, "manifests": ["package.json"]})
        self.assertTrue(res["guardrail"]["triggered"])
        self.assertIn("exceeds 48", " ".join(res["guardrail"]["reasons"]))

    def test_size_cap_relaxes_on_large_scope(self):
        small = group({"files": [f"src/m{i % 4}/f{i}.ts" for i in range(12)],
                       "manifests": ["package.json"]})
        large = group({"files": [f"src/m{i % 4}/f{i:02d}.ts" for i in range(40)],
                       "manifests": ["package.json"]})
        self.assertEqual(small["size_cap"], 4)
        self.assertEqual(large["size_cap"], 6)

    def test_no_edges_falls_back_to_directory_axis(self):
        res = group({"files": ["a/x.ts", "b/y.ts", "c/z.ts"]})
        self.assertEqual(res["grouping_strategy"], "S1")
        self.assertEqual(res["cut_ratio"], 0.0)
        self.assertEqual(res["edge_count"], 0)

    def test_single_group_takes_fast_path(self):
        res = group({"files": ["src/a.ts", "src/b.ts", "src/c.ts"]})
        self.assertEqual(res["group_count"], 1)
        self.assertEqual(res["path"], "fast")

    def test_two_files_take_fast_path(self):
        self.assertEqual(group({"files": ["a/x.ts", "b/y.ts"]})["path"], "fast")

    def test_empty_scope_is_not_an_error(self):
        res = group({"files": []})
        self.assertEqual(res["group_count"], 0)
        self.assertTrue(res["coverage_ok"])

    def test_rejects_malformed_input(self):
        r = run([PY, GROUP], stdin=json.dumps({"nope": 1}))
        self.assertEqual(r.returncode, 2)

    def test_windows_separators_normalize(self):
        res = group({"files": ["src\\a\\x.ts", "src\\a\\y.ts"]})
        self.assertTrue(all("\\" not in f for f in res["in_diff_files"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
