---
name: forge
description: Transform documentation into actionable development plans with task breakdown and status tracking. Combines deep-* thoroughness with superpowers organization.
---

# Code Forge - Documentation to Implementation

Forge executable development plans from documentation, combining deep-* thoroughness with superpowers organization.

## When to Use

- Have existing requirements/design documentation that needs to be broken down into development tasks
- Need team collaboration with plans committed to Git
- Need to track development progress (pending, in_progress, completed)
- Need iterative development with pause/resume support

## Workflow

```
Input Document → Analysis → Planning → Task Breakdown → Execution → Status Tracking
```

## Detailed Implementation Steps

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

### Step 0.7: Handle No-Argument Invocation (Feature Dashboard)

When `/forge` is called **without arguments**, display a dashboard of all features.

#### 0.7.1 Scan for Features

1. Resolve the output directory: `<base_dir>/<output_dir>/`
2. Search for all `state.json` files: `<output_dir>/*/state.json` (one level deep)
3. For each `state.json`, extract: `feature`, `status`, `progress.*`, `metadata.source_doc`, `updated`

#### 0.7.2 Display Feature Dashboard

**Features found:** Show table with #, Feature, Progress, Status, Last Updated. Offer actions:
- Enter a number to continue that feature
- New feature — start from a document
- Exit

**No features found:** Show empty state with instructions:
- How to create a feature document at `{base_dir}/{input_dir}/{feature-name}.md`
- How to run `/forge @path/to/feature.md`

#### 0.7.3 Update Project-Level Overview

After scanning, regenerate `{output_dir}/overview.md` using Step 8.5 logic.

#### 0.7.4 Handle User Selection

- **Number selected** → read that feature's `state.json`, enter resume mode (same as Step 1.5 resume)
- **"New feature"** → ask for document path via `AskUserQuestion`, proceed to Step 1
- **"Exit"** → end

---

### Step 1: Validate Input Document

#### 1.1 Check Document Path

User should provide an @file path:
```bash
/forge @planning/features/user-auth.md
```

**Note:** Use configured path (`{base_dir}/{input_dir}/`)

#### 1.2-1.4 Validate Document and Handle Errors

Perform these checks on the provided document:

1. **File exists** — if not found, list available files in `{input_dir}/` and suggest corrections (check for typos)
2. **File is not empty** — if empty, suggest adding requirements content with a minimal example
3. **File is Markdown** — if not `.md`, warn and ask whether to continue as plain text

If no document is provided and dashboard was not shown: display usage instructions with examples.

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

### Step 2: Analyze Document Content

Analyze the following:
1. **Feature Name** — extract from filename or document title
2. **Technical Requirements** — identify mentioned tech stack, frameworks
3. **Functional Scope** — understand what needs to be implemented
4. **Constraints** — performance, security, compatibility requirements
5. **Testing Requirements** — check if testing strategy is mentioned

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

### Step 5: Generate overview.md

Generate feature overview with these required sections:

- **Overview** — extract or summarize from source document
- **Scope** — included and excluded items
- **Technology Stack** — language/framework, key dependencies, testing tools
- **Task Execution Order** — table: #, Task File (linked to `./tasks/`), Description, Status
- **Progress** — total/completed/in_progress/pending counts
- **Reference Documents** — link to source document

### Step 6: Generate plan.md

Create implementation plan with these required sections:

- **Goal** — one sentence describing what to implement
- **Architecture Design** — component structure, data flow, technical choices with rationale
- **Task Breakdown** — dependency graph (mermaid `graph TD`) + task list with estimated time and dependencies
- **Risks and Considerations** — identified technical challenges
- **Acceptance Criteria** — checklist (tests pass, code review, docs, performance)
- **References** — related technical docs and examples

### Step 7: Task Breakdown

Create `tasks/{name}.md` for each task.

**Principles:**
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
- When resuming from dashboard (Step 0.7)
- After feature completion (Step 12)

Display: `📋 Project overview updated: {output_dir}/overview.md`

---

### Step 9: Display Plan

Output plan summary:
```
✅ Implementation plan generated

📂 Location: {output_dir}/{feature_name}/
📋 Total Tasks: {count}
⏱️  Estimated Total Time: {estimate}

Task Overview:
  {id}  - {title}  [{status}]
  ...

View detailed plan:
  cat {output_dir}/{feature_name}/plan.md
```

### Step 10: Ask for Execution Method

Use `AskUserQuestion`:

- **"Start Execution Now (Recommended)"** — execute tasks one by one, auto-track progress → enter Step 11
- **"Manual Execution Later"** — save plan, show resume instructions (`/forge` or `/forge @doc`)
- **"Team Collaboration Mode"** — show guidelines: commit plan to Git, claim tasks via `assignee`, sync `state.json`
- **"Generate Plan Only"** — only generate plan files, stop here

### Step 11: Task Execution Loop

1. Read `state.json`
2. Find the next task in `execution_order` that is `"pending"` with no unmet dependencies
3. If no such task exists: display "All tasks completed!" and exit loop
4. Display: "Starting task: {id} - {title}"
5. Read the task file `tasks/{id}.md`
6. Update task status to `"in_progress"` in `state.json`
7. Execute the task steps (follow TDD: write tests → run tests → implement → verify → commit)
8. Ask user via `AskUserQuestion`: "Is the task completed?"
   - **"Completed, continue to next"** → update status to `"completed"`, continue loop
   - **"Encountered issue, pause"** → keep `"in_progress"`, exit loop
   - **"Skip this task"** → update status to `"skipped"`, continue loop
9. Repeat from step 1

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
2. Regenerate the project-level overview (`{output_dir}/overview.md`) using Step 8.5 logic

```
🎉 Feature implementation completed!

✅ Completed tasks: {completed}/{total}
📂 Location: {output_dir}/{feature_name}/
⏱️  Total time: {actual_time}

Next steps:
  [ ] Run complete test suite
  [ ] Code review
  [ ] Update documentation
  [ ] Create Pull Request
```

## Integration with Claude Code Tasks

Optionally synchronize tasks to Claude Code's Task system:
- For each task in `execution_order`, call `TaskCreate` with:
  - `subject`: `"<task_id>: <task_title>"`
  - `description`: contents of the task file
  - `activeForm`: `"Implementing <task_title>"`

## Coordination with Other Skills

- **With /brainstorming**: Brainstorm design first → generate `planning/features/xxx-design.md` → `/forge @planning/features/xxx-design.md`
- **With /test-driven-development**: Automatically call TDD skill when executing each task
- **With /requesting-code-review**: After all tasks completed → `/requesting-code-review`

## Notes

1. **Document Quality**: The more detailed the input document, the more accurate the generated plan
2. **Git Commits**: Recommend committing the planning directory and `.code-forge.json` to Git for team visibility
3. **State Files**: `state.json` can be optionally committed or added to .gitignore
4. **Task Granularity**: Recommend 1-3 hours per task for easy tracking
5. **Dependency Management**: Dependencies between tasks affect execution order
6. **Project Overview**: The project-level `overview.md` in `{output_dir}/` is auto-generated and shows all features, dependencies, and recommended implementation order
7. **Tool Discovery**: `.code-forge.json` contains a `_tool` section with the plugin URL — new team members can find and install the tool from there
8. **Status Definitions**: `pending`, `in_progress`, `completed`, `blocked`, `skipped`
9. **Directory Structure**:
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
10. **Naming Conventions**: Feature directories use kebab-case (`user-auth`). Task files use descriptive names (`setup.md`). No "claude-" or tool prefixes. Suitable for Git commits.

## Examples

Complete examples can be found at:
- `examples/user-auth/` - User authentication feature example
- `examples/file-upload/` - File upload feature example
