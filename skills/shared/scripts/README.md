# code-forge script layer

Deterministic helpers that absorb the mechanical, token-heavy bookkeeping the
skills used to do by hand: config resolution, `state.json` read/mutate, and
status rendering. The model keeps the *reasoning* (planning, review, fixing);
these scripts keep the *record-keeping*.

## Runtime contract

- **Python 3 standard library only.** No third-party packages, no `pip install`,
  no network. Runs anywhere `python3` exists.
- Each CLI is a single file with `--help`. `cf_common.py` is the shared library
  the three CLIs import (they live in the same directory, so the import resolves
  even when a script is invoked by absolute path).
- These scripts are the **single source of truth** for the logic they encode.
  The skill prose says "run the script, use its output" rather than restating
  the algorithm, so the two cannot drift.
- **Graceful degradation:** every skill that calls a script keeps a manual
  fallback for when `python3` is unavailable. Switch to it silently — never
  stop or ask the user.

## Locating the scripts at runtime

A skill runs from the *user's* project directory, not from the code-forge
install — so a project-cwd glob will not find these scripts. Resolve the path
from the **install** instead, once per session, and reuse it (full procedure in
`configuration.md` → *Locating the script layer*):

1. **Preferred:** `<cf_scripts>` is `../shared/scripts/` relative to the skill
   you are running — the *same* installation, so the script version matches the
   skill version. Do not borrow scripts from a different (possibly stale) cached
   install.
2. **Fallback discovery** (follows symlinks, bash- and zsh-safe):

   ```bash
   find -L ~/.agents/skills ~/.claude/skills ~/.claude/plugins/cache \
     -maxdepth 7 -type f -name cf_common.py -path '*code-forge*/skills/shared/scripts/*' \
     2>/dev/null | head -1     # use the parent dir
   ```
3. Verify `cf_common.py` exists before use; otherwise fall back to the manual
   path in the skill.

Invoke as `python3 "<cf_scripts>/<script>.py" ...`, quoting both the script path
and any project file arguments (project paths may contain spaces).

## Scripts

### `cf-config.py` — configuration resolver (read-only)
Implements config Step 0: project-root detection, the three-layer merge
(system defaults → `~/.code-forge.json` → `<root>/.code-forge.json`),
validation, the `--tmp` override, and directory resolution. Prints one JSON
object: `project_root, config, base_dir, input_dir, output_dir, tmp_mode,
sources, errors`. On a validation error it reports the error and falls back to
system defaults. Never writes files (gitignore safety for `--tmp` stays in the
skill prose). Used by every skill's Step 0.

```bash
python3 cf-config.py [--root PATH] [--tmp]
```

### `cf-state.py` — state.json operations
The `state.json` schema and every mutation. Recomputes the `progress` block,
the feature-level `status`, and task timestamps so callers never hand-edit JSON.
Used by `impl` (loop) and `plan` (scaffold).

```bash
cf-state.py show <state.json>                       # compact summary + recomputed progress
cf-state.py next <state.json>                        # next runnable pending task (or ALL_DONE)
cf-state.py set-status <state.json> <task> <status>  # status ∈ pending|in_progress|completed|skipped|blocked
cf-state.py recompute <state.json>                   # rebuild progress + overall status
cf-state.py init --feature NAME [--source-doc DOC] [--output PATH]  # tasks (JSON array) on stdin
```

`init` topologically sorts task dependencies into `execution_order` and errors
non-zero on a cycle.

### `cf-status.py` — dashboard / detail renderer
Scans `<output_dir>/*/state.json` and `.code-forge/tmp/*/state.json`, recomputes
progress, and prints a ready-to-display table — the raw state files never enter
context. Used by `status`. When `--output-dir` is omitted it resolves the output
directory the same way `cf-config.py` does.

```bash
cf-status.py [--root PATH] [--output-dir DIR]            # project dashboard
cf-status.py [--root PATH] [--output-dir DIR] <feature>  # feature detail
```

### `cf-verify-plan.py` — plan structure validator
Checks a feature plan directory the way impl Step 4 and plan Step 12 do:
required files exist and are non-empty, `state.json` is valid and internally
consistent (fields present, `execution_order` ↔ `tasks` IDs match, referenced
task files exist), and the markdown docs contain their required sections.
Structural problems are errors (non-zero exit); content/cosmetic problems are
warnings. `--strict` promotes warnings to errors (use it for plan Step 12).

```bash
cf-verify-plan.py <feature_dir> [--output-dir DIR] [--root PATH] [--strict]
```

### `cf-scan.py` — project facts collector (read-only)
One-pass enumeration for the project-analysis protocol (PA.1/PA.2.1/PA.5):
language mix, build files, dependency names, detected frameworks, test files +
framework + command, source-tree top level, entrypoints, and best-effort
signals (database/auth/queue/jobs/external-api). A FACTS COLLECTOR, not an
analyst — architecture, call graph, and risk assessment stay with the model.
Used by `plan`, `impl`, `review`, `fix`, `debug`, `tdd` (any codebase-aware
workflow).

```bash
cf-scan.py [--root PATH] [--max-tree N]
```

Add `--json` to the state/status/verify commands for machine-readable output;
`cf-config.py` and `cf-scan.py` always emit JSON.

## Tests

`python3 skills/shared/scripts/test_scripts.py` — standard-library `unittest`
covering `cf_common` plus every CLI end-to-end.
