### Step 0: Configuration Detection and Loading

**Important:** Detect and load configuration before any operation.

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
- `directories.base` must NOT contain `..` (security risk)
- `directories.base` must NOT be a system/source directory (`src/`, `node_modules/`, `build/`, `.git/`)
- `git.commit_state_file` must be boolean (not string `"true"`)
- `execution.default_mode` must be one of: `"ask"`, `"manual"`, `"auto"`

On validation failure: display all errors with descriptions, then continue with system defaults.

#### 0.4 Show Configuration Summary and Continue

Display a brief configuration summary showing:
- Base/input/output directories
- Configuration sources detected (system defaults, user config, project config)

Then **proceed directly** — no "Continue?" confirmation needed.

#### 0.6 Store Configuration Context

Track resolved values for subsequent steps:
- `config` — final merged configuration object
- `project_root` — detected project root path
- `base_dir` — resolved: `<project_root>/<config.directories.base>`
- `input_dir` — resolved: `<base_dir>/<config.directories.input>`
- `output_dir` — resolved: `<base_dir>/<config.directories.output>`
