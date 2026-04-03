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

(Coordinator: use the actual `output_dir` where you found `state.json` in MR-2 — either `planning/` or `.code-forge/tmp/`.)

```
Implement the feature '{feature_name}' in this repository.

1. Read {output_dir}/{feature_name}/state.json to find pending tasks
2. For each pending task in execution_order:
   a. Read the task file from tasks/ directory
   b. Follow TDD: write tests -> run tests (expect fail) -> implement -> run tests (expect pass)
   c. Commit changes with a descriptive message after tests pass
   d. Update the task status to "completed" in state.json
3. If a task is blocked (dependencies unmet, missing files), mark it as "blocked" in state.json and continue to the next task
4. After all tasks: update the feature status in state.json
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
