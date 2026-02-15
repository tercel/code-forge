# Subcommand Architecture & Prompt Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the monolithic `forge/SKILL.md` into 5 independent subcommand skills (plan, impl, status, fixbug, review), rewrite `forge.md` as a router, and add direct prompt-to-document support.

**Architecture:** Follows the spec-forge orchestrator pattern — a main `forge.md` router parses arguments and dispatches to independent skill files. Each skill inlines its own Step 0 config loading. New `fixbug` and `review` workflows are fully new skills.

**Tech Stack:** Markdown skill files (Claude Code plugin system), no runtime code.

**Design doc:** `docs/plans/2026-02-15-subcommands-and-prompt-support-design.md`

---

### Task 1: Rewrite `commands/forge.md` as Router

**Files:**
- Modify: `commands/forge.md`

**Step 1: Overwrite `commands/forge.md` with the router implementation**

```markdown
---
description: "Transform documentation into actionable development plans with status tracking"
argument-hint: "[plan|impl|status|fixbug|review] <args>"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

You are the code-forge orchestrator. Your job is to route subcommands or default to status dashboard.

The user invoked: `/forge $ARGUMENTS`

## Step 1: Parse Arguments

Parse `$ARGUMENTS` into `subcommand` and `remaining_args`:

| Rule | Condition | subcommand | remaining_args |
|------|-----------|-----------|----------------|
| 1 | Empty (no arguments) | `status` | — |
| 2 | First word is `plan`, `impl`, `status`, `fixbug`, or `review` | that word | everything after the first word |
| 3 | First word starts with `@` | `plan` | entire `$ARGUMENTS` |
| 4 | Any other text | `plan` | entire `$ARGUMENTS` (prompt mode) |

**Examples:**

| Input | subcommand | remaining_args |
|-------|-----------|----------------|
| (empty) | `status` | — |
| `plan @planning/features/auth.md` | `plan` | `@planning/features/auth.md` |
| `plan 实现用户登录` | `plan` | `实现用户登录` |
| `impl user-auth` | `impl` | `user-auth` |
| `status` | `status` | — |
| `status user-auth` | `status` | `user-auth` |
| `fixbug 登录报500` | `fixbug` | `登录报500` |
| `review user-auth` | `review` | `user-auth` |
| `@planning/features/auth.md` | `plan` | `@planning/features/auth.md` |
| `实现用户登录` | `plan` | `实现用户登录` |

## Step 2: Route

Invoke the corresponding skill, passing `remaining_args` as context:

| subcommand | Action |
|-----------|--------|
| `plan` | Invoke `code-forge:plan` skill with `remaining_args` |
| `impl` | Invoke `code-forge:impl` skill with `remaining_args` |
| `status` | Invoke `code-forge:status` skill with `remaining_args` |
| `fixbug` | Invoke `code-forge:fixbug` skill with `remaining_args` |
| `review` | Invoke `code-forge:review` skill with `remaining_args` |
```

**Step 2: Verify the file**

Run: `head -5 commands/forge.md`
Expected: YAML frontmatter with `argument-hint: "[plan|impl|status|fixbug|review] <args>"`

**Step 3: Commit**

```bash
git add commands/forge.md
git commit -m "refactor: rewrite forge.md as subcommand router"
```

---

### Task 2: Create Subcommand Alias Files

**Files:**
- Create: `commands/plan.md`
- Create: `commands/impl.md`
- Create: `commands/status.md`
- Create: `commands/fixbug.md`
- Create: `commands/review.md`

**Step 1: Create `commands/plan.md`**

```markdown
---
description: "Analyze documentation and generate implementation plan"
argument-hint: "[@feature-doc.md | \"requirement description\"]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:plan skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
```

**Step 2: Create `commands/impl.md`**

```markdown
---
description: "Execute pending tasks for a feature"
argument-hint: "[feature-name]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:impl skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
```

**Step 3: Create `commands/status.md`**

```markdown
---
description: "Display feature dashboard and progress"
argument-hint: "[feature-name]"
allowed-tools: [Read, Glob, Grep, Write, AskUserQuestion, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:status skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
```

**Step 4: Create `commands/fixbug.md`**

```markdown
---
description: "Debug and fix bugs with interactive upstream trace-back"
argument-hint: "[\"bug description\" | @issue.md]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:fixbug skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
```

**Step 5: Create `commands/review.md`**

```markdown
---
description: "Review code quality for a completed feature"
argument-hint: "[feature-name]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:review skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
```

**Step 6: Verify all files exist**

Run: `ls -la commands/`
Expected: 6 files — `forge.md`, `plan.md`, `impl.md`, `status.md`, `fixbug.md`, `review.md`

**Step 7: Commit**

```bash
git add commands/plan.md commands/impl.md commands/status.md commands/fixbug.md commands/review.md
git commit -m "feat: add subcommand alias files for plan, impl, status, fixbug, review"
```

---

### Task 3: Create `skills/plan/SKILL.md`

This is the largest file. It extracts Step 0, adds new Step 0.8, then includes Steps 1-9 from the original `skills/forge/SKILL.md`. Step 0.7 (dashboard) moves to status skill. Steps 10-12 move to impl skill.

**Files:**
- Create: `skills/plan/SKILL.md`

**Step 1: Create directory**

Run: `mkdir -p skills/plan`

**Step 2: Write `skills/plan/SKILL.md`**

Write the file with this exact content — it combines the original Steps 0, 1-9 plus the new Step 0.8 for prompt support:

````markdown
---
name: plan
description: Analyze documentation (or a prompt) and generate an implementation plan with task breakdown, TDD steps, and progress tracking.
---

# Code Forge — Plan

Generate an implementation plan from a feature document or a requirement prompt.

## When to Use

- Have a feature document that needs to be broken into development tasks
- Have a requirement idea (text prompt) that needs planning
- Need a structured plan with TDD task breakdown

## Workflow

```
Input (Document or Prompt) → Analysis → Planning → Task Breakdown → Status Tracking
```

## Context Management

Steps 2, 6, and 7 are offloaded to sub-agents via the `Task` tool to prevent context window exhaustion on large projects. The main context retains only concise summaries returned by each sub-agent, while full document analysis, file generation, and code implementation happen in isolated sub-agent contexts that are discarded after completion.

**Actual execution order:** 0 → 0.8 (prompt mode only) → 1 → **2 (sub-agent)** → 3 → 4 → **6 (sub-agent)** → **7 (sub-agent)** → 5 → 8 → 8.5 → 9

Step 5 (overview.md) executes after Steps 6 and 7 because it references task files generated by those steps.

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
   - `directories.base` = `"planning/"`, `directories.input` = `"features/"`, `directories.output` = `"implementation/"`
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
- Resolved file creation path: `{base_dir}/{output_dir}/{feature_name}/`

Then **proceed directly** — no "Continue?" confirmation needed.

**Error handling:**
- Config file not found → note "using defaults" and continue
- Config file parse error → show error, fall back to defaults, continue
- Invalid config values → show warnings, fall back to defaults for invalid fields, continue

#### 0.6 Store Configuration Context

Track resolved values for subsequent steps:
- `config` — final merged configuration object
- `project_root` — detected project root path
- `base_dir` — resolved: `<project_root>/<config.directories.base>`
- `input_dir` — resolved: `<base_dir>/<config.directories.input>`
- `output_dir` — resolved: `<base_dir>/<config.directories.output>`

---

### Step 0.8: Prompt to Document (Prompt Mode Only)

**This step only runs when the input is NOT a file path (does NOT start with `@`).**

If the input starts with `@`, skip directly to Step 1.

#### 0.8.1 Generate Slug

Convert the prompt text to a kebab-case slug for the filename:
- ASCII text: lowercase, replace spaces/special chars with hyphens (e.g., "User Login Feature" → `user-login-feature`)
- Non-ASCII text (Chinese, Japanese, etc.): use `AskUserQuestion` to let user confirm or provide a custom slug. Suggest a reasonable English slug based on the prompt meaning.

#### 0.8.2 Check for Existing Document

Check if `{input_dir}/{slug}.md` already exists:
- **Exists** → ask via `AskUserQuestion`:
  - "Append to existing document" — append the prompt text under a new `## Additional Requirements` section
  - "Overwrite" — replace the file
  - "Use existing document as-is" — skip writing, proceed with existing file
- **Does not exist** → continue

#### 0.8.3 Generate Minimal Feature Document

Write `{input_dir}/{slug}.md` with minimal content:

```markdown
# {Feature Title}

## Requirements

{user's original prompt text, verbatim}

## Notes

- Generated from prompt by code-forge
- Created: {ISO timestamp}
```

**Design principles:**
- Document is minimal — only wraps the user's original text, no AI expansion
- Expansion and analysis happen in Step 2 (sub-agent) as normal
- All subsequent steps see a standard file path, unaware of input source

#### 0.8.4 Set File Path

Set the generated file path as the current input document path (prefixed with `@`), then continue to Step 1.

---

### Step 1: Validate Input Document

#### 1.1 Check Document Path

User should provide an @file path:
```bash
/forge plan @planning/features/user-auth.md
```

**Note:** Use configured path (`{base_dir}/{input_dir}/`)

#### 1.2-1.4 Validate Document and Handle Errors

Perform these checks on the provided document:

1. **File exists** — if not found, list available files in `{input_dir}/` and suggest corrections (check for typos)
2. **File is not empty** — if empty, suggest adding requirements content with a minimal example
3. **File is Markdown** — if not `.md`, warn and ask whether to continue as plain text

If no document is provided and Step 0.8 was not triggered: display usage instructions with examples.

On any error: display the issue, suggest a fix, and stop.

#### 1.5 Detect Existing Plan

Check whether `<output_dir>/<feature_name>/` already exists:

- **Has `state.json`** → **Resume mode**: show progress summary (task statuses), ask via `AskUserQuestion`:
  - Continue (recommended) — resume from current progress
  - Restart — delete all files and regenerate
  - View plan — open plan.md
  - Cancel

- **Directory exists but no `state.json`** → **Conflict mode**: warn about existing files, ask:
  - Backup and overwrite — move to `.backup/` then regenerate
  - Force overwrite — overwrite directly
  - Cancel — handle manually then rerun

### Step 2: Analyze Document Content (via Sub-agent)

**Offload to sub-agent** to keep the full document content out of the main context.

Spawn a `Task` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Analyze feature document"`

**Sub-agent prompt must include:**
- The input document file path (so the sub-agent reads it, NOT the main context)
- Instruction to return ONLY a structured summary

**Sub-agent must analyze and return:**
1. **Feature Name** — extracted from filename or document title (kebab-case)
2. **Technical Requirements** — tech stack, frameworks, languages mentioned
3. **Functional Scope** — 2-3 sentence summary of what needs to be implemented
4. **Constraints** — performance, security, compatibility requirements
5. **Testing Requirements** — testing strategy mentioned, or "not specified"
6. **Key Components** — major modules/components to build (bulleted list)
7. **Estimated Complexity** — low/medium/high with brief rationale

**Main context retains:** Only the structured summary returned by the sub-agent (~1-2KB). The full document content stays in the sub-agent's context and is discarded.

**Important:** Store the returned summary for use in Steps 3 and 6.

### Step 3: Ask for Additional Information

If not clearly specified in the document, use a **single** `AskUserQuestion` combining up to 3 questions. Skip any question already answered by the document:

**Question 1: Technology Stack Confirmation**
- "Use {extracted_tech} mentioned in document"
- "Use existing project tech stack" — analyze project code, use existing frameworks
- "Custom" — user specifies

**Question 2: Testing Strategy**
- "Strict TDD (Recommended)" — write tests first for each task
- "Tests After" — implement first, write tests at end
- "Minimal Testing" — test only core logic

**Question 3: Task Granularity**
- "Fine-grained (5-10 tasks)" — each task 1-2 hours
- "Medium-grained (3-5 tasks)" — each task half day
- "Coarse-grained (2-3 tasks)" — each task 1-2 days

### Step 4: Create Directory Structure

Extract feature name from filename or document title (convert to kebab-case).

Create directory structure and **proceed directly** — no confirmation needed:
```
{output_dir}/{feature_name}/
├── overview.md
├── plan.md
├── tasks/
└── state.json
```

### Step 6: Generate plan.md (via Sub-agent)

**Offload to sub-agent** to keep plan generation output out of the main context.

Spawn a `Task` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Generate implementation plan"`

**Sub-agent prompt must include:**
- The input document file path (sub-agent re-reads the original for full context)
- The structured summary from Step 2 (paste it into the prompt)
- User answers from Step 3 (tech stack choice, testing strategy, task granularity)
- The output file path: `{output_dir}/{feature_name}/plan.md`
- Instructions to write the plan file AND return a concise task list summary

**Sub-agent must write `plan.md`** with these required sections:
- **Goal** — one sentence describing what to implement
- **Architecture Design** — component structure, data flow, technical choices with rationale
- **Task Breakdown** — dependency graph (mermaid `graph TD`) + task list with estimated time and dependencies
- **Risks and Considerations** — identified technical challenges
- **Acceptance Criteria** — checklist (tests pass, code review, docs, performance)
- **References** — related technical docs and examples

**Sub-agent must return** (as response text, separate from the file it writes) a concise task list summary:

    TASK_COUNT: <number>
    TASKS:
    - <task_id>: <task_title> [depends on: <deps or "none">] (~<estimated_time>)
    - <task_id>: <task_title> [depends on: <deps or "none">] (~<estimated_time>)
    ...
    EXECUTION_ORDER: <task_id_1>, <task_id_2>, ...

**Main context retains:** Only the task list summary (~1-2KB). The full plan content is on disk.

### Step 7: Task Breakdown (via Sub-agent)

**Offload to sub-agent** to keep task file generation out of the main context.

Spawn a `Task` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Generate task breakdown files"`

**Sub-agent prompt must include:**
- The plan file path: `{output_dir}/{feature_name}/plan.md` (sub-agent reads it from disk)
- The task list summary returned by Step 6 (paste it into the prompt)
- The tasks directory path: `{output_dir}/{feature_name}/tasks/`
- All the principles and format requirements below

**Sub-agent must create `tasks/{name}.md`** for each task, following these principles:
- TDD first: test → implement → verify
- Concrete steps: include code examples and commands
- Traceable: annotate dependencies (depends on / required by)

**Each task file must include:**
- **Goal** — what this task accomplishes
- **Files Involved** — files to create/modify
- **Steps** — numbered, with code examples where helpful
- **Acceptance Criteria** — checklist
- **Dependencies** — depends on / required by
- **Estimated Time**

**Naming:** Use descriptive filenames (`setup.md`, `models.md` — no numeric prefixes). Execution order is defined in `overview.md` and `state.json`, not in filenames.

**Sub-agent must return** (as response text) the list of generated files:

    GENERATED_FILES:
    - tasks/<task_id>.md: <task_title>
    - tasks/<task_id>.md: <task_title>
    ...

**Main context retains:** Only the file list (~0.5KB). All task file content is on disk.

### Step 5: Generate overview.md

**Execution order:** This step executes AFTER Steps 6 and 7. Use the task list summary returned by the Step 6 sub-agent and the file list returned by the Step 7 sub-agent to populate task-related sections.

Generate feature overview with these required sections:

- **Overview** — extract or summarize from source document
- **Scope** — included and excluded items
- **Technology Stack** — language/framework, key dependencies, testing tools
- **Task Execution Order** — table: #, Task File (linked to `./tasks/`), Description, Status
- **Progress** — total/completed/in_progress/pending counts
- **Reference Documents** — link to source document

### Step 8: Initialize state.json

Create `state.json` with these required fields:

| Field | Description |
|-------|-------------|
| `feature` | Feature name (string) |
| `created`, `updated` | ISO timestamps |
| `status` | `"pending"` initially |
| `execution_order` | Array of task IDs in execution order |
| `progress` | `{ total_tasks, completed, in_progress, pending }` |
| `tasks` | Array of task objects (see below) |
| `metadata` | `{ source_doc, created_by: "code-forge", version: "1.0" }` |

Each task object in the `tasks` array:

| Field | Description |
|-------|-------------|
| `id` | Task identifier (matches filename without `.md`) |
| `file` | Relative path: `tasks/{id}.md` |
| `title` | Human-readable task title |
| `status` | `"pending"` initially |
| `started_at`, `completed_at` | ISO timestamps or `null` |
| `assignee` | `null` initially |
| `commits` | Empty array `[]` initially |

### Step 8.5: Generate/Update Project-Level Overview

After initializing `state.json`, generate or update `{output_dir}/overview.md` — a bird's-eye view of all features.

#### 8.5.1 Scan and Analyze

1. Scan `{output_dir}/*/state.json` for all existing features
2. Read each feature's `overview.md` and `plan.md` for descriptions and dependencies
3. Determine implementation order based on actual dependencies (not alphabetical)

#### 8.5.2 Generate Overview

Create or overwrite `{output_dir}/overview.md` with these required sections:

- **Overall Progress** — progress bar + module counts (completed/in_progress/pending)
- **Module Overview** — table: #, Module (linked to directory), Description, Status, Progress
- **Module Dependencies** — mermaid dependency graph
- **Recommended Implementation Order** — phased with rationale ("Why first", "Why next")

**Key principles:**
- Implementation order must reflect actual dependencies
- Status aggregated from `state.json` files (not manually maintained)
- Use relative links to feature directories

#### 8.5.3 When to Regenerate

- After creating a new feature plan (this step)
- After feature completion

Display: `Project overview updated: {output_dir}/overview.md`

---

### Step 9: Display Plan and Next Steps

Output plan summary:
```
Implementation plan generated

Location: {output_dir}/{feature_name}/
Total Tasks: {count}
Estimated Total Time: {estimate}

Task Overview:
  {id}  - {title}  [{status}]
  ...

Next steps:
  /forge impl {feature_name}     Execute tasks
  /forge status {feature_name}   View progress
  cat {output_dir}/{feature_name}/plan.md   View detailed plan
```

## Integration with Claude Code Tasks

Optionally synchronize tasks to Claude Code's Task system:
- For each task in `execution_order`, call `TaskCreate` with:
  - `subject`: `"<task_id>: <task_title>"`
  - `description`: contents of the task file
  - `activeForm`: `"Implementing <task_title>"`

## Coordination with Other Skills

- **With /brainstorming**: Brainstorm design first → generate feature doc → `/forge plan @feature-doc.md`
- **With /forge impl**: After plan generated → `/forge impl {feature}` to execute
- **With /forge review**: After implementation → `/forge review {feature}` to review

## Notes

1. **Document Quality**: The more detailed the input document, the more accurate the generated plan
2. **Prompt Mode**: When using prompt mode, the generated document is minimal. Step 2 sub-agent analysis handles expansion.
3. **Git Commits**: Recommend committing the planning directory and `.code-forge.json` to Git for team visibility
4. **State Files**: `state.json` can be optionally committed or added to .gitignore
5. **Task Granularity**: Recommend 1-3 hours per task for easy tracking
6. **Dependency Management**: Dependencies between tasks affect execution order
7. **Project Overview**: The project-level `overview.md` in `{output_dir}/` is auto-generated and shows all features, dependencies, and recommended implementation order
8. **Tool Discovery**: `.code-forge.json` contains a `_tool` section with the plugin URL — new team members can find and install the tool from there
9. **Status Definitions**: `pending`, `in_progress`, `completed`, `blocked`, `skipped`
10. **Directory Structure**:
    ```
    planning/
    ├── features/              # Input: feature documents
    │   └── user-auth.md
    └── implementation/        # Output: implementation plans
        ├── overview.md        # Project-level overview (auto-generated)
        └── {feature}/         # Per-feature directory
            ├── overview.md    # Feature overview + task execution order
            ├── plan.md        # Implementation plan
            ├── tasks/         # Task breakdown files
            └── state.json     # Status tracking
    ```
11. **Naming Conventions**: Feature directories use kebab-case (`user-auth`). Task files use descriptive names (`setup.md`). No "claude-" or tool prefixes. Suitable for Git commits.
````

**Step 3: Verify file structure**

Run: `wc -l skills/plan/SKILL.md`
Expected: ~300+ lines

**Step 4: Commit**

```bash
git add skills/plan/SKILL.md
git commit -m "feat: create plan skill — analysis and plan generation (Steps 0-9)"
```

---

### Task 4: Create `skills/impl/SKILL.md`

**Files:**
- Create: `skills/impl/SKILL.md`

**Step 1: Create directory**

Run: `mkdir -p skills/impl`

**Step 2: Write `skills/impl/SKILL.md`**

````markdown
---
name: impl
description: Execute pending tasks for a feature — TDD-driven implementation with sub-agent isolation and progress tracking.
---

# Code Forge — Impl

Execute pending implementation tasks for a feature, following the plan generated by `/forge plan`.

## When to Use

- Have a generated plan (`state.json` + `tasks/` directory) ready for execution
- Need to resume a partially completed feature
- Need task-by-task execution with TDD and progress tracking

## Workflow

```
Locate Feature → Confirm Execution → Task Loop (sub-agents) → Verify → Complete
```

## Context Management

Step 11 dispatches a dedicated sub-agent for each task, so code changes from one task don't pollute the context of the next. The main context only handles coordination: reading state, dispatching sub-agents, and updating status.

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
   - `directories.base` = `"planning/"`, `directories.input` = `"features/"`, `directories.output` = `"implementation/"`
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

---

### Step 1: Locate Feature

#### 1.1 With Feature Name Argument

If the user provided a feature name (e.g., `/forge impl user-auth`):

1. Look for `{output_dir}/{feature_name}/state.json`
2. If not found, search `{output_dir}/*/state.json` for a feature whose `feature` field matches
3. If still not found, show error: "Feature '{feature_name}' not found. Run `/forge status` to see available features."

#### 1.2 Without Argument

If no feature name is provided:

1. Scan `{output_dir}/*/state.json` for all features
2. Filter to features with `status` = `"pending"` or `"in_progress"` (exclude `"completed"`)
3. If none found: "No features ready for execution. Run `/forge plan` to create one."
4. If one found: use it automatically
5. If multiple found: display table and use `AskUserQuestion` to let user select

#### 1.3 Validate Feature State

After locating the feature:
1. Read `state.json`
2. Check that `tasks` array is non-empty
3. Check that task files in `tasks/` directory exist
4. Show feature progress summary: completed/in_progress/pending counts
5. If all tasks are `"completed"`: "All tasks already completed. Run `/forge review {feature}` to review."

---

### Step 10: Ask for Execution Method

Use `AskUserQuestion`:

- **"Start Execution Now (Recommended)"** — execute tasks one by one, auto-track progress → enter Step 11
- **"Manual Execution Later"** — save plan, show resume instructions (`/forge impl {feature}`)
- **"Team Collaboration Mode"** — show guidelines: commit plan to Git, claim tasks via `assignee`, sync `state.json`
- **"Generate Plan Only"** — only generate plan files, stop here

### Step 11: Task Execution Loop (via Sub-agents)

**Each task is executed by a dedicated sub-agent** to prevent cross-task context accumulation. The main context only handles coordination: reading state, dispatching sub-agents, and updating status.

#### 11.1 Coordination Loop (Main Context)

1. Read `state.json`
2. Find the next task in `execution_order` that is `"pending"` with no unmet dependencies
3. If no such task exists: display "All tasks completed!" and exit loop
4. Display: "Starting task: {id} - {title}"
5. Update task status to `"in_progress"` in `state.json`
6. **Dispatch sub-agent** for this task (see 11.2)
7. Review the sub-agent's execution summary
8. Ask user via `AskUserQuestion`: "Is the task completed?"
   - **"Completed, continue to next"** → update status to `"completed"`, continue loop
   - **"Encountered issue, pause"** → keep `"in_progress"`, exit loop
   - **"Skip this task"** → update status to `"skipped"`, continue loop
9. Repeat from step 1

#### 11.2 Task Execution Sub-agent

Spawn a `Task` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Execute task: {task_id}"`

**Sub-agent prompt must include:**
- The task file path: `{output_dir}/{feature_name}/tasks/{task_id}.md` (sub-agent reads it)
- The project root path
- Tech stack and testing strategy (from state.json metadata or plan.md)
- Instruction to follow TDD: write tests → run tests → implement → verify
- Instruction to return ONLY a concise execution summary

**Sub-agent executes:**
1. Read the task file from disk
2. Follow the task steps (TDD: write tests → run tests → implement → verify)
3. Commit changes if all tests pass (with descriptive commit message)

**Sub-agent must return** a concise execution summary:

    STATUS: completed | partial | blocked
    FILES_CHANGED:
    - path/to/file.ext (created | modified)
    - ...
    TEST_RESULTS: X passed, Y failed
    SUMMARY: <1-2 sentence description of what was done>
    ISSUES: <any blockers or concerns, or "none">

**Main context retains:** Only the execution summary (~0.5-1KB per task). All code changes, test outputs, and file reads stay in the sub-agent's context and are discarded.

#### 11.3 Parallel Execution (Optional)

When multiple pending tasks have **no mutual dependencies** (none depends on another), they may be dispatched as parallel sub-agents using multiple `Task` tool calls in a single message. Each sub-agent works in isolation on its own task.

**Use parallel execution only when:**
- Tasks modify different files (no overlap in "Files Involved")
- Tasks have no dependency relationship (neither `depends on` the other)
- User has agreed to parallel execution

After all parallel sub-agents complete, review each summary and update `state.json` for all completed tasks before continuing the loop.

### Step 11.5: Verify Generated Files

Before completion summary, verify all generated files:

**Checks:**
1. Required files exist and are non-empty: `overview.md`, `plan.md`, `state.json`
2. `tasks/` directory exists and contains `.md` files with descriptive names
3. `state.json` is valid JSON with required fields (`feature`, `status`, `tasks`, `execution_order`); task count matches task files; all IDs in `execution_order` match `tasks` entries
4. `plan.md` contains: title heading, `## Goal`, `## Task Breakdown`, `## Acceptance Criteria`
5. `overview.md` contains `## Task Execution Order` table

**On pass:** Show checklist with all items passing, continue.

**On error (missing required files):** Show what's missing. Attempt auto-fix:
- Empty `overview.md` → generate template from plan data
- Missing `tasks/` → create directory
- Missing `state.json` → generate initial state from task files found
Then re-verify.

**On warnings (count mismatch, missing optional section):** Show warnings, continue by default.

---

### Step 12: Completion Summary

After all tasks are completed:

1. Update `state.json` with final status
2. Regenerate the project-level overview (`{output_dir}/overview.md`)

```
Feature implementation completed!

Completed tasks: {completed}/{total}
Location: {output_dir}/{feature_name}/
Total time: {actual_time}

Next steps:
  /forge review {feature_name}   Review code quality
  /forge status {feature_name}   View final status
```
````

**Step 3: Commit**

```bash
git add skills/impl/SKILL.md
git commit -m "feat: create impl skill — task execution loop (Steps 10-12)"
```

---

### Task 5: Create `skills/status/SKILL.md`

**Files:**
- Create: `skills/status/SKILL.md`

**Step 1: Create directory**

Run: `mkdir -p skills/status`

**Step 2: Write `skills/status/SKILL.md`**

````markdown
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
   - `directories.base` = `"planning/"`, `directories.input` = `"features/"`, `directories.output` = `"implementation/"`
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
  /forge plan @doc.md          Create new plan from document
  /forge plan "requirement"    Create new plan from prompt
  /forge impl <feature>        Execute tasks for a feature
  /forge status <feature>      View feature detail
  /forge fixbug "description"  Debug a bug
  /forge review <feature>      Review completed feature
```

Offer actions via `AskUserQuestion`:
- Enter a feature name to view its detail
- Start a new plan
- Exit

**No features found:** Show empty state with instructions:
- How to create a feature document at `{base_dir}/{input_dir}/{feature-name}.md`
- How to run `/forge plan @path/to/feature.md` or `/forge plan "requirement text"`

#### 2.3 Update Project-Level Overview

After scanning, regenerate `{output_dir}/overview.md` using Step 4 logic.

#### 2.4 Handle User Selection

- **Feature name selected** → show Feature Detail (Step 3)
- **"New plan"** → suggest `/forge plan` command
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
Source: planning/features/user-auth.md
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
  /forge impl user-auth      Continue execution
  /forge review user-auth    Review completed tasks
  /forge fixbug "..."        Fix a bug in this feature
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
````

**Step 3: Commit**

```bash
git add skills/status/SKILL.md
git commit -m "feat: create status skill — dashboard and progress tracking"
```

---

### Task 6: Create `skills/fixbug/SKILL.md`

**Files:**
- Create: `skills/fixbug/SKILL.md`

**Step 1: Create directory**

Run: `mkdir -p skills/fixbug`

**Step 2: Write `skills/fixbug/SKILL.md`**

````markdown
---
name: fixbug
description: Debug and fix bugs with interactive upstream trace-back — diagnoses root cause level, confirms upstream document updates, and applies TDD fixes.
---

# Code Forge — Fixbug

Systematically debug and fix bugs with interactive trace-back to upstream documents (task descriptions, plans, requirements).

## When to Use

- Encountered a bug or unexpected behavior in a feature
- Need to diagnose whether the root cause is in code, task description, plan, or requirements
- Want to fix the bug with TDD and keep upstream documents in sync

## Workflow

```
Bug Input → Context Scan → Feature Association → Root Cause Diagnosis → Trace-back Confirmation → TDD Fix → Doc Sync → Summary
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
   - `directories.base` = `"planning/"`, `directories.input` = `"features/"`, `directories.output` = `"implementation/"`
   - `git.auto_commit` = `false`, `git.commit_state_file` = `true`, `git.gitignore_patterns` = `[]`
   - `execution.default_mode` = `"ask"`, `execution.auto_tdd` = `true`, `execution.task_granularity` = `"medium"`

2. **User global config** (`~/.code-forge.json`, if exists) → deep-merge into defaults

3. **Project config** (`<project_root>/.code-forge.json`, if exists) → deep-merge (highest priority)

#### 0.3-0.6 Validate, Show Summary, Store Context

Same as other skills — validate config, display summary, store resolved paths (`config`, `project_root`, `base_dir`, `input_dir`, `output_dir`). Proceed directly.

---

### Step 1: Receive Bug Description

Accept input in two modes:
- **Prompt text** (e.g., `/forge fixbug 登录页面报500错误`) — use the text as bug description
- **File reference** (e.g., `/forge fixbug @issues/bug-123.md`) — read the file for bug details

If no input provided, use `AskUserQuestion` to ask: "Describe the bug you encountered."

Store the bug description for subsequent steps.

---

### Step 2: Project Context Scan

Scan the project codebase to understand the context:

1. Use `Glob` to get project structure overview
2. Use `Grep` to search for keywords from the bug description in the codebase
3. Identify files and modules likely related to the bug
4. Note the tech stack and testing framework used

Store a concise context summary (~500 words).

---

### Step 3: Associate Feature (If Exists)

Attempt to associate the bug with an existing code-forge feature:

1. Search `{output_dir}/*/state.json` for all features
2. For each feature, check if the bug-related files overlap with the feature's task files (read `tasks/*.md` → "Files Involved" sections)
3. **Match found** → load the feature's `plan.md` and relevant `tasks/*.md` as additional context. Note the feature name.
4. **No match found** → mark as standalone bug. Skip upstream trace-back (Steps 5 and 7). Proceed with code-only fix.

If multiple features match, use `AskUserQuestion` to let user select the most relevant one.

---

### Step 4: Root Cause Diagnosis

**Offload to sub-agent** for deep analysis.

Spawn a `Task` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Diagnose bug root cause"`

**Sub-agent prompt must include:**
- Bug description
- Project context summary from Step 2
- Feature context (plan.md, task files) if associated in Step 3
- Instruction to: reproduce the bug, identify the root cause, classify the root cause level

**Root cause levels:**

| Level | Description | Example |
|-------|------------|---------|
| 1 | Code bug | Logic error, boundary miss, typo, wrong variable |
| 2 | Incomplete task description | Task.md steps missing a case, wrong acceptance criteria |
| 3 | Plan design flaw | Architecture doesn't handle a scenario, missing component |
| 4 | Incomplete requirement doc | Original feature doc missing a requirement |

**Sub-agent must return:**

    ROOT_CAUSE_LEVEL: <1-4>
    ROOT_CAUSE_SUMMARY: <1-2 sentence description>
    AFFECTED_FILES:
    - path/to/file.ext: <what's wrong>
    UPSTREAM_DOCS_AFFECTED: (only if Level >= 2)
    - Level 2: tasks/<task>.md — <what's missing/wrong>
    - Level 3: plan.md — <what's missing/wrong>
    - Level 4: {input_dir}/<feature>.md — <what's missing/wrong>
    PROPOSED_FIX: <brief fix description>
    REGRESSION_TEST: <what test to write>

---

### Step 5: Interactive Trace-back Confirmation

**This step only runs if Level >= 2 AND the bug is associated with a feature.**

Present the root cause analysis to the user, then confirm upstream updates level by level.

#### 5.1 Present Analysis

Display:
```
Root Cause Analysis

Level: {level} — {level_description}
Summary: {root_cause_summary}

Affected code:
  {affected_files list}

Upstream documents affected:
  {upstream_docs_affected list}
```

#### 5.2 Per-Level Confirmation

For each affected upstream level (from lowest to highest), use `AskUserQuestion`:

"Root cause traced to **{level_name}**: `{doc_path}` — {what's wrong}. Update this document?"

Options:
- **"Yes, update this document"** → mark for update in Step 7
- **"No, code fix only"** → skip this level, do not modify this document
- **"Show proposed changes"** → display the proposed diff for this document, then re-ask

#### 5.3 Generate Fix Plan

Compile the fix plan:
- Code changes to make (always)
- Upstream documents to update (based on user confirmations)
- Regression test to write

---

### Step 6: TDD Fix

Execute the fix following TDD methodology:

#### 6.1 Write Regression Test

Write a test that reproduces the bug:
- Test must FAIL with the current code (proving the bug exists)
- Test must describe the expected correct behavior

Run the test to verify it fails.

#### 6.2 Implement Fix

Make the minimal code changes to fix the bug.

Run the regression test to verify it passes.

#### 6.3 Run Full Test Suite

Run the project's full test suite to ensure no regressions:
- If tests pass: continue
- If tests fail: investigate and fix before proceeding

#### 6.4 Commit Fix

Commit the code changes with a descriptive message:
```
fix: {brief description of bug fix}
```

---

### Step 7: Upstream Document Sync

**This step only runs if upstream documents were confirmed for update in Step 5.**

For each confirmed document update:

#### 7.1 Show Diff Preview

Before modifying each document, show the proposed changes in diff format:
```
--- a/{doc_path}
+++ b/{doc_path}
@@ ... @@
- old content
+ new content
```

Ask user: "Apply this change?" (Yes / No / Edit manually)

#### 7.2 Apply Changes

- **Level 2** (task.md): Update the task's steps, acceptance criteria, or files involved
- **Level 3** (plan.md): Update architecture, task breakdown, or risk sections
- **Level 4** (feature doc): Update requirements or scope

#### 7.3 Commit Document Updates

Commit upstream document changes separately from code fix:
```
docs: update {doc_path} — traced from bug fix
```

---

### Step 8: Update state.json

If the bug is associated with a feature:

1. Read the feature's `state.json`
2. Add a `fixes` array (if not present) to the feature-level metadata
3. Append a fix record:
   ```json
   {
     "bug": "brief bug description",
     "root_cause_level": 2,
     "root_cause": "brief root cause",
     "fixed_files": ["path/to/file.ext"],
     "commits": ["abc1234"],
     "doc_updates": ["tasks/auth-logic.md"],
     "fixed_at": "ISO timestamp"
   }
   ```
4. Update `state.json` `updated` timestamp

If standalone bug (no associated feature): skip this step.

---

### Step 9: Summary

Display fix summary:

```
Bug Fix Complete

Bug: {description}
Root Cause: Level {level} — {summary}

Code Changes:
  {files changed}

Regression Test:
  {test file and name}

Document Updates:
  {list of updated docs, or "none"}

Commits:
  {commit hashes}

Next steps:
  /forge status {feature}    View updated progress
  /forge review {feature}    Review all changes
```
````

**Step 3: Commit**

```bash
git add skills/fixbug/SKILL.md
git commit -m "feat: create fixbug skill — debugging with upstream trace-back"
```

---

### Task 7: Create `skills/review/SKILL.md`

**Files:**
- Create: `skills/review/SKILL.md`

**Step 1: Create directory**

Run: `mkdir -p skills/review`

**Step 2: Write `skills/review/SKILL.md`**

````markdown
---
name: review
description: Review code quality for a completed feature — checks code, tests, security, and plan consistency.
---

# Code Forge — Review

Review the code quality of a feature's implementation against its plan, checking code quality, test coverage, security, and consistency.

## When to Use

- Feature implementation is complete or nearly complete
- Want to verify code quality before creating a PR
- Need a structured review against the original plan

## Workflow

```
Locate Feature → Collect Changes → Multi-Dimension Review (sub-agent) → Generate Report → Update State → Summary
```

## Context Management

The review analysis is offloaded to a sub-agent to handle large diffs without exhausting the main context.

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
   - `directories.base` = `"planning/"`, `directories.input` = `"features/"`, `directories.output` = `"implementation/"`
   - `git.auto_commit` = `false`, `git.commit_state_file` = `true`, `git.gitignore_patterns` = `[]`
   - `execution.default_mode` = `"ask"`, `execution.auto_tdd` = `true`, `execution.task_granularity` = `"medium"`

2. **User global config** (`~/.code-forge.json`, if exists) → deep-merge into defaults

3. **Project config** (`<project_root>/.code-forge.json`, if exists) → deep-merge (highest priority)

#### 0.3-0.6 Validate, Show Summary, Store Context

Same as other skills — validate config, display summary, store resolved paths. Proceed directly.

---

### Step 1: Locate Feature

#### 1.1 With Feature Name Argument

If the user provided a feature name (e.g., `/forge review user-auth`):

1. Look for `{output_dir}/{feature_name}/state.json`
2. If not found: show error, list available features

#### 1.2 Without Argument

If no feature name:

1. Scan `{output_dir}/*/state.json` for all features
2. Filter to features with at least one `"completed"` task
3. If none: "No features with completed tasks to review."
4. If one: use it automatically
5. If multiple: use `AskUserQuestion` to let user select

#### 1.3 Load Feature Context

1. Read `state.json`
2. Read `plan.md` (for acceptance criteria and architecture)
3. Note completed task count and overall progress

---

### Step 2: Collect Change Scope

#### 2.1 From Commits

Extract all commit hashes from `state.json` → `tasks[].commits`:
- Flatten all commit arrays into a single list
- If commits are recorded, use `git diff` between the earliest and latest commits
- If no commits recorded, fall back to scanning files involved in tasks

#### 2.2 From Task Files

Read all `tasks/*.md` files and collect their "Files Involved" sections:
- Build a complete list of files created/modified by this feature
- Read current state of each file

#### 2.3 Summary

Store:
- Total files changed
- Total lines added/removed (from git diff)
- List of all affected files

---

### Step 3: Multi-Dimension Review (via Sub-agent)

**Offload to sub-agent** to handle the full diff analysis.

Spawn a `Task` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Review feature: {feature_name}"`

**Sub-agent prompt must include:**
- Feature name and `plan.md` file path
- List of all affected files (sub-agent reads them)
- The acceptance criteria from `plan.md`
- Instructions to review across all dimensions below

**Review dimensions:**

#### 3.1 Code Quality
- Naming conventions: consistent, descriptive, follows project style
- Code structure: appropriate abstractions, no unnecessary complexity
- DRY: no duplicated logic
- Error handling: appropriate error handling at boundaries
- Comments: only where logic isn't self-evident

#### 3.2 Test Coverage
- Every task has corresponding tests
- Tests cover happy path, edge cases, and error cases
- Tests are independent and deterministic
- Test names describe the behavior being tested

#### 3.3 Security
- OWASP top 10 check: SQL injection, XSS, CSRF, etc.
- No hardcoded secrets or credentials
- Input validation at system boundaries
- Proper authentication/authorization checks

#### 3.4 Plan Consistency
- All acceptance criteria from `plan.md` are met
- Architecture matches the design in `plan.md`
- No unplanned features added (scope creep)
- All planned tasks are implemented

**Sub-agent must return:**

    REVIEW_SUMMARY:
      overall_rating: <pass | pass_with_notes | needs_changes>
      total_issues: <number>

    CODE_QUALITY:
      rating: <good | acceptable | needs_work>
      issues:
      - severity: <critical | warning | suggestion>
        file: path/to/file.ext
        line: <number or range>
        description: <what's wrong>
        suggestion: <how to fix>

    TEST_COVERAGE:
      rating: <good | acceptable | needs_work>
      coverage_gaps:
      - <description of untested scenario>

    SECURITY:
      rating: <pass | warning | critical>
      issues:
      - <description of security concern>

    PLAN_CONSISTENCY:
      criteria_met: <X/Y>
      unmet_criteria:
      - <criterion not met>
      scope_issues:
      - <unplanned additions or missing planned features>

---

### Step 4: Generate Review Report

Write review report to `{output_dir}/{feature_name}/review.md`:

```markdown
# Code Review: {feature_name}

**Date:** {ISO date}
**Reviewer:** code-forge
**Overall Rating:** {pass | pass_with_notes | needs_changes}

## Summary

{1-2 paragraph summary of the review findings}

## Code Quality

**Rating:** {rating}

{issues table or "No issues found"}

## Test Coverage

**Rating:** {rating}

{coverage gaps or "All scenarios covered"}

## Security

**Rating:** {rating}

{security issues or "No security concerns"}

## Plan Consistency

**Criteria Met:** {X/Y}

{unmet criteria or "All criteria met"}

## Recommendations

{prioritized list of changes to make}

## Verdict

{final assessment and recommendation: merge, fix then merge, or rework}
```

---

### Step 5: Update state.json

1. Read `state.json`
2. Add or update `review` field in metadata:
   ```json
   {
     "review": {
       "date": "ISO timestamp",
       "rating": "pass_with_notes",
       "total_issues": 3,
       "report": "review.md"
     }
   }
   ```
3. Update `state.json` `updated` timestamp

---

### Step 6: Summary and Next Steps

Display:

```
Code Review Complete: {feature_name}

Rating: {overall_rating}
Issues: {total_issues} ({critical} critical, {warning} warnings, {suggestion} suggestions)
Report: {output_dir}/{feature_name}/review.md

{If needs_changes:}
Recommended actions:
  1. {highest priority fix}
  2. {next priority fix}
  ...
  After fixing: /forge review {feature_name}   Re-run review

{If pass or pass_with_notes:}
Ready for next steps:
  /forge status {feature_name}         View final status
  Create a Pull Request
```
````

**Step 3: Commit**

```bash
git add skills/review/SKILL.md
git commit -m "feat: create review skill — code quality review workflow"
```

---

### Task 8: Delete Old Skill and Update Plugin Metadata

**Files:**
- Delete: `skills/forge/SKILL.md`
- Delete: `skills/forge/` (directory)
- Modify: `.claude-plugin/plugin.json`

**Step 1: Delete old skill directory**

Run: `rm -rf skills/forge`

**Step 2: Verify deletion**

Run: `ls skills/`
Expected: `plan/  impl/  status/  fixbug/  review/` (no `forge/`)

**Step 3: Update `.claude-plugin/plugin.json`**

Change version to `0.5.0` and update description:

```json
{
  "name": "code-forge",
  "description": "Forge executable, TDD-driven implementation plans from documentation — with subcommands for planning, execution, debugging, and review",
  "version": "0.5.0",
  "author": {
    "name": "tercel",
    "url": "https://github.com/tercel"
  },
  "repository": "https://github.com/tercel/code-forge",
  "license": "MIT",
  "keywords": ["planning", "tdd", "task-breakdown", "implementation", "documentation", "debugging", "code-review"]
}
```

**Step 4: Commit**

```bash
git add -A skills/forge .claude-plugin/plugin.json
git commit -m "refactor: remove old forge skill, bump version to 0.5.0"
```

---

### Task 9: Update README.md

**Files:**
- Modify: `README.md`

**Step 1: Read current README.md**

Read the file to understand its current structure.

**Step 2: Update the Usage section**

Replace or update the usage/commands section to document the new subcommand architecture. Ensure these sections exist:

1. **Quick Start** — show the most common usage patterns
2. **Commands** — document all subcommands with descriptions and examples:

```markdown
## Commands

| Command | Description |
|---------|------------|
| `/forge` | Dashboard — show all features and progress |
| `/forge plan @doc.md` | Generate plan from a feature document |
| `/forge plan "requirement"` | Generate plan from a text prompt |
| `/forge impl [feature]` | Execute pending tasks for a feature |
| `/forge status [feature]` | View dashboard or feature detail |
| `/forge fixbug "description"` | Debug and fix a bug with upstream trace-back |
| `/forge review [feature]` | Review code quality for a feature |

All subcommands are also available as direct aliases:
`/forge:plan`, `/forge:impl`, `/forge:status`, `/forge:fixbug`, `/forge:review`
```

3. **Subcommand Details** — brief description of each subcommand's purpose

Preserve existing sections that are still relevant (Configuration, Directory Structure, etc.).

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README with subcommand architecture and prompt support"
```

---

## Verification Checklist

After all tasks are complete, verify:

- [ ] `commands/` contains 6 files: `forge.md`, `plan.md`, `impl.md`, `status.md`, `fixbug.md`, `review.md`
- [ ] `skills/` contains 5 directories: `plan/`, `impl/`, `status/`, `fixbug/`, `review/` (no `forge/`)
- [ ] Each `skills/*/SKILL.md` has YAML frontmatter with `name` and `description`
- [ ] `forge.md` routes all 5 subcommands correctly
- [ ] `plugin.json` version is `0.5.0`
- [ ] Old `skills/forge/` directory is deleted
- [ ] README documents new subcommand architecture
