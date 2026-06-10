### Impl Multi-Repo Definitions

**Input parsing (MR-1):**
- `feature_name` — the feature to implement (required, single token before `--repos`, no spaces). This is also the `{input_summary}` used throughout the protocol.
- Usage: `/code-forge:impl <feature-name> --repos <repo1> <repo2> [repo3...]`
- Example: `/code-forge:impl core-dispatcher --repos ~/apcore-python ~/apcore-typescript ~/apcore-rust`

**Readiness check (MR-2):**
- Look for `{output_dir}/{feature_name}/state.json` in each repo
- Also check `.code-forge/tmp/{feature_name}/state.json` (plan may have been created with `--tmp`)
- If not found: repo is **not ready** — suggest running `/code-forge:plan` for that repo
- If found: read `state.json`, extract task count and completion progress

**Summary table columns (MR-2):** `Tasks` — show task count and completion (e.g., "6 tasks (0 done)")

**Sub-agent prompt (MR-4):**

(Coordinator: use the actual `output_dir` where you found `state.json` in MR-2 — either `planning/` or `.code-forge/tmp/`. Substitute `{cf_scripts}` with the absolute scripts path passed in the dispatch prompt — `<cf_install>/skills/shared/scripts` — so the sub-agent reuses the same deterministic state helper as single-repo impl.)

```
Implement the feature '{feature_name}' in this repository.

State updates use the code-forge state helper at "{cf_scripts}/cf-state.py"
(absolute path). If python3 is unavailable, edit state.json by hand instead:
set the task status, fix started_at/completed_at, and recompute the progress
block and feature-level status. Let STATE = {output_dir}/{feature_name}/state.json.

1. Get the next task: python3 "{cf_scripts}/cf-state.py" next "STATE"
   (prints `id<TAB>title`, or `ALL_DONE`).
2. While not ALL_DONE, for that task id:
   a. python3 "{cf_scripts}/cf-state.py" set-status "STATE" <id> in_progress
   b. Read the task file from the tasks/ directory
   c. Follow TDD: write tests -> run (expect fail) -> implement -> run (expect pass)
   d. Commit changes with a descriptive message after tests pass
   e. set-status <id> completed  (or `blocked` if dependencies unmet / files missing)
   f. Go back to step 1
3. After the loop: python3 "{cf_scripts}/cf-state.py" recompute "STATE"
```

**Result format (MR-4 output):**

```
TASKS_COMPLETED: N/M
FILES_CHANGED:
- path/to/file.ext (created | modified)
TEST_RESULTS: X passed, Y failed
```

**Report columns (MR-5):** `Tasks` and `Tests` — e.g., "6/6" and "42 passed, 0 failed"

**Next steps (MR-5):**
- For partial repos: `/code-forge:impl {feature_name}` (in that repo to resume)
- For completed repos: `/code-forge:review {feature_name}`
- General: `/code-forge:verify`
