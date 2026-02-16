---
name: status
description: Display feature dashboard, progress tracking, and project-level overview.
---

# Code Forge — Status

Display a dashboard of all features or detailed progress for a specific feature.

## When to Use

- Want to see all features and their progress
- Want to check status of a specific feature
- Need to regenerate the project-level overview

## Workflow

```
Load Config → Scan Features → Display Dashboard or Detail → Update Overview
```

## Detailed Steps

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
   - `_tool.skills_collection` = `"https://github.com/tercel/claude-code-skills"` (read-only)
   - `directories.base` = `""`, `directories.input` = `"docs/features/"`, `directories.output` = `"planning/"`
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

Display a brief configuration summary. Then **proceed directly**.

#### 0.6 Store Configuration Context

Track resolved values:
- `config`, `project_root`, `base_dir`, `input_dir`, `output_dir`

---

### Step 1: Determine Mode

Based on arguments:
- **No argument** → Global Dashboard (Step 2)
- **Feature name provided** → Feature Detail (Step 3)

---

### Step 2: Global Dashboard

#### 2.1 Scan for Features

1. Resolve the output directory: `<base_dir>/<output_dir>/`
2. Search for all `state.json` files: `<output_dir>/*/state.json` (one level deep)
3. For each `state.json`, extract: `feature`, `status`, `progress.*`, `metadata.source_doc`, `updated`

#### 2.2 Display Feature Dashboard

**Features found:** Show table with #, Feature, Progress, Status, Last Updated.

```
code-forge — Feature Dashboard

  #  | Feature        | Progress   | Status      | Last Updated
  1  | user-auth      | 3/5 (60%)  | in_progress | 2026-02-14
  2  | file-upload    | 0/3 (0%)   | pending     | 2026-02-13
  3  | notifications  | 4/4 (100%) | completed   | 2026-02-12

Commands:
  /code-forge:plan @doc.md          Create new plan from document
  /code-forge:plan "requirement"    Create new plan from prompt
  /code-forge:impl <feature>        Execute tasks for a feature
  /code-forge:status <feature>      View feature detail
  /code-forge:fixbug "description"  Debug a bug
  /code-forge:review <feature>      Review completed feature
```

Offer actions via `AskUserQuestion`:
- Enter a feature name to view its detail
- Start a new plan
- Exit

**No features found:** Show empty state with instructions:
- How to create a feature document at `{base_dir}/{input_dir}/{feature-name}.md`
- How to run `/code-forge:plan @path/to/feature.md` or `/code-forge:plan "requirement text"`

#### 2.3 Update Project-Level Overview

After scanning, regenerate `{output_dir}/overview.md` using Step 4 logic.

#### 2.4 Handle User Selection

- **Feature name selected** → show Feature Detail (Step 3)
- **"New plan"** → suggest `/code-forge:plan` command
- **"Exit"** → end

---

### Step 3: Feature Detail

#### 3.1 Locate Feature

1. Look for `{output_dir}/{feature_name}/state.json`
2. If not found: show error, list available features

#### 3.2 Display Feature Detail

Read `state.json` and display:

```
code-forge — Feature: user-auth

Status: in_progress
Source: docs/features/user-auth.md
Created: 2026-02-10
Updated: 2026-02-14

Tasks:
  #  | Task           | Status      | Started     | Completed
  1  | setup          | completed   | 2026-02-10  | 2026-02-10
  2  | models         | completed   | 2026-02-11  | 2026-02-11
  3  | auth-logic     | in_progress | 2026-02-14  | —
  4  | api-endpoints  | pending     | —           | —
  5  | integration    | pending     | —           | —

Progress: 2/5 (40%)

Commands:
  /code-forge:impl user-auth      Continue execution
  /code-forge:review user-auth    Review completed tasks
  /code-forge:fixbug "..."        Fix a bug in this feature
```

---

### Step 4: Generate/Update Project-Level Overview

#### 4.1 Scan and Analyze

1. Scan `{output_dir}/*/state.json` for all existing features
2. Read each feature's `overview.md` and `plan.md` for descriptions and dependencies
3. Determine implementation order based on actual dependencies (not alphabetical)

#### 4.2 Generate Overview

Create or overwrite `{output_dir}/overview.md` with these required sections:

- **Overall Progress** — progress bar + module counts (completed/in_progress/pending)
- **Module Overview** — table: #, Module (linked to directory), Description, Status, Progress
- **Module Dependencies** — mermaid dependency graph
- **Recommended Implementation Order** — phased with rationale ("Why first", "Why next")

**Key principles:**
- Implementation order must reflect actual dependencies
- Status aggregated from `state.json` files (not manually maintained)
- Use relative links to feature directories

Display: `Project overview updated: {output_dir}/overview.md`
