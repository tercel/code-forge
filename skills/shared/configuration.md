### Step 0: Configuration Detection and Loading

**Important:** Detect and load configuration before any operation.

#### Fast path (preferred): run the resolver script

code-forge ships a deterministic resolver so root detection, the three-layer
config merge, validation, and path resolution never have to be done by hand
(it is also more reliable than hand-merging JSON).

1. **Locate the scripts directory once** and reuse it for the whole session:
   Glob `**/skills/shared/scripts/cf_common.py` and take its parent directory.
   Call it `<cf_scripts>`.
2. Run, from the project root:

   ```bash
   python3 "<cf_scripts>/cf-config.py" [--tmp]
   ```

3. Parse the JSON it prints and use these fields directly: `project_root`,
   `config`, `base_dir`, `input_dir`, `output_dir`, `tmp_mode`, `sources`,
   `errors`.
4. If `errors` is non-empty, display each error; the resolver has already
   fallen back to system defaults, so continue with the values it returned.
5. Show a one-line config summary (base/input/output + `sources`) and
   **proceed directly** — no confirmation needed.
6. For `--tmp`: after the resolver reports `tmp_mode: true`, ensure
   `.code-forge/` is gitignored (`git check-ignore -q .code-forge/` || append
   `**/.code-forge/` to `.gitignore`) and show the temporary-mode notice. The
   resolver is read-only and never edits `.gitignore`.

If `python3` is unavailable or the script cannot be found, use the manual
fallback below to produce the same resolved values by hand. Do not stop or ask
the user — switch to the fallback silently.

#### Manual fallback: configuration detection and loading

#### 0.1 Detect Project Root

Search upward for project root markers:
```
.git/ | .code-forge.json | pyproject.toml | package.json | Cargo.toml | go.mod | build.gradle | pom.xml | Makefile
```

If no root is found, use the current directory as the project root.

#### 0.2 Load Configuration (three-layer merge)

Load configuration by priority (each layer deep-merges into previous):

1. **System defaults:**
   - `_tool.name` = `"code-forge"` (read-only, not overridable)
   - `_tool.description` = `"Transform documentation into actionable development plans with task breakdown and status tracking"` (read-only)
   - `_tool.url` = `"https://github.com/tercel/code-forge"` (read-only)
   - `directories.base` = `""`, `directories.input` = `"docs/features/"`, `directories.output` = `"planning/"` (**NOT** `docs/plans/` — always `planning/`)
   - `git.auto_commit` = `false`, `git.commit_state_file` = `true`, `git.gitignore_patterns` = `[]`
   - `execution.default_mode` = `"ask"`, `execution.auto_tdd` = `true`, `execution.task_granularity` = `"medium"`

2. **User global config** (`~/.code-forge.json`, if exists) → deep-merge into defaults

3. **Project config** (`<project_root>/.code-forge.json`, if exists) → deep-merge (highest priority)

#### 0.3 Validate Configuration

Validation rules:
- `directories.base`, `directories.input`, and `directories.output` must NOT contain `..` (security risk — path traversal)
- `directories.base`, `directories.input`, and `directories.output` must NOT start with `/` (must be relative paths)
- `directories.base` must NOT be a system/source directory (`src/`, `node_modules/`, `build/`, `.git/`)
- `git.commit_state_file` must be boolean (not string `"true"`)
- `execution.default_mode` must be one of: `"ask"`, `"manual"`, `"auto"`

On validation failure: display all errors with descriptions, then continue with system defaults.

#### 0.4 Show Configuration Summary and Continue

Display a brief configuration summary showing:
- Base/input/output directories
- Configuration sources detected (system defaults, user config, project config)

Then **proceed directly** — no "Continue?" confirmation needed.

#### 0.5 Handle `--tmp` Flag

If the user's arguments include `--tmp`:

1. Override `output_dir` to `<project_root>/.code-forge/tmp/`
2. Ensure `.code-forge/` is in `.gitignore` (same logic as worktree's gitignore safety — check with `git check-ignore -q .code-forge/`, add if not ignored)
3. Display: `Temporary mode: plan files will be written to .code-forge/tmp/ (gitignored, not committed)`

**Note:** `--tmp` only affects `output_dir`. Input directory and all other config remain unchanged.

#### 0.6 Store Configuration Context

Track resolved values for subsequent steps:
- `config` — final merged configuration object
- `project_root` — detected project root path
- `base_dir` — resolved: `<project_root>/<config.directories.base>`
- `input_dir` — resolved: `<base_dir>/<config.directories.input>`
- `output_dir` — resolved: `<base_dir>/<config.directories.output>` (or `<project_root>/.code-forge/tmp/` if `--tmp`)
- `tmp_mode` — boolean, `true` if `--tmp` was used
