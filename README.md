# Code Forge

> Transform documentation into actionable development plans with task breakdown, TDD steps, and progress tracking.

## Commands

| Command | Description |
|---------|------------|
| `/code-forge:plan @doc.md` | Generate plan from a feature document |
| `/code-forge:plan @dir/` | Browse a directory and pick a feature to plan |
| `/code-forge:plan "requirement"` | Generate plan from a text prompt |
| `/code-forge:impl [feature]` | Execute pending tasks for a feature |
| `/code-forge:status [feature]` | View dashboard or feature detail |
| `/code-forge:fixbug "description"` | Debug and fix a bug with upstream trace-back |
| `/code-forge:review [feature]` | Review code quality for a feature |
| `/code-forge:port @docs --ref impl --lang java` | Port a project to a new language |

Each subcommand is a standalone slash command — invoke directly without a router.

---

## Subcommand Details

### plan — Generate Implementation Plan

Analyzes a feature document (or text prompt) and generates an implementation plan with architecture design, task breakdown, and TDD steps.

**Input modes:**

```bash
# From a specific file
/code-forge:plan @docs/features/user-auth.md

# From a directory — lists features for selection
/code-forge:plan @docs/features/
/code-forge:plan @../../other-project         # External project OK

# From a text prompt — auto-creates feature doc first
/code-forge:plan "Implement JWT-based user authentication"
```

**What it does:**
1. Reads and analyzes the feature document (via sub-agent)
2. Asks for tech stack, testing strategy, and task granularity
3. Generates `plan.md` with architecture design and task dependency graph
4. Creates `tasks/*.md` with TDD-first steps, code examples, and acceptance criteria
5. Generates `overview.md` with task execution order table (controls execution sequence)
6. Initializes `state.json` for progress tracking
7. Updates project-level `planning/overview.md` with all features and dependencies

**Directory mode:** When given a directory path, plan scans for `*.md` files (tries `docs/features/`, `features/`, then root) and lets you pick one. Works with external paths — the document doesn't need to be in the current project.

**Prompt mode:** When given text instead of a path, auto-delegates to `spec-forge:feature` to generate a feature spec, then plans from that.

**Reference docs:** Configure `reference_docs.sources` in `.code-forge.json` to inject existing project documentation as context into plan generation.

---

### impl — Execute Tasks

Executes pending tasks for a feature using isolated sub-agents. Each task runs in its own sub-agent to prevent context exhaustion.

```bash
# Execute a specific feature
/code-forge:impl user-auth

# Auto-select — picks the next pending/in-progress feature
/code-forge:impl
```

**What it does:**
1. Locates the feature's `state.json`
2. Finds the next pending task respecting dependency order
3. Dispatches a sub-agent to execute: write tests → run → implement → verify → commit
4. After each task, asks: completed / pause / skip
5. Supports parallel execution for independent tasks

**Pause/resume:** Stop anytime. Progress is saved in `state.json`. Re-run `/code-forge:impl` to continue where you left off.

---

### status — Project Dashboard

Displays a dashboard of all features or detailed progress for a specific feature.

```bash
# Global dashboard — all features
/code-forge:status

# Feature detail — tasks and progress
/code-forge:status user-auth
```

**Dashboard shows:**
- Feature name, progress %, status, last updated
- Actions: view detail, start new plan, continue impl

**Feature detail shows:**
- Task table with status, start/complete timestamps
- Actions: continue impl, run review, debug

Auto-regenerates `planning/overview.md` on each run.

---

### fixbug — Debug with Upstream Trace-back

Systematically debugs bugs with root cause diagnosis at 4 levels. Keeps upstream documents in sync with code fixes.

```bash
# From a description
/code-forge:fixbug "Login page returns 500 when email has special characters"

# From a file
/code-forge:fixbug @bug-report.md
```

**Root cause levels:**

| Level | Root Cause | Action |
|-------|-----------|--------|
| 1 | Code bug (logic error, boundary miss) | Fix code only |
| 2 | Incomplete task description | Fix code + update task.md |
| 3 | Plan design flaw | Fix code + update plan.md |
| 4 | Incomplete requirements | Fix code + update feature spec |

**What it does:**
1. Scans project context and locates related code
2. Associates bug with a code-forge feature (if exists)
3. Diagnoses root cause level (sub-agent)
4. Interactively confirms upstream document updates per level
5. Applies TDD fix: regression test → implement → verify
6. Updates upstream docs and `state.json`

Works on any project — does not require prior code-forge setup. If no feature is associated, runs as a standalone fix without upstream trace-back.

---

### review — Code Quality Review

Reviews completed feature code across 4 dimensions and generates a structured report.

```bash
# Review a specific feature
/code-forge:review user-auth

# Auto-select completed feature
/code-forge:review
```

**Review dimensions:**

| Dimension | What it checks |
|-----------|---------------|
| Code Quality | Naming, structure, DRY, SOLID principles |
| Test Coverage | Unit/integration/e2e, coverage %, missing tests |
| Security | OWASP top 10, SQL injection, XSS, CSRF, auth |
| Plan Consistency | Does code match plan.md architecture? |

**Output:** Review report displayed in terminal; summary saved to `state.json`. Use `--save` to persist as `planning/{feature}/review.md`.

---

### port — Cross-Language Porting

Ports a documentation-driven project to a new target language. Initializes the target project, analyzes the reference implementation, and batch-generates plans for all selected features.

```bash
/code-forge:port @../apcore --ref apcore-python --lang java
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `@<docs-project>` | Yes | Documentation project with `docs/features/*.md` |
| `--ref <name>` | No | Reference implementation (uses its `planning/` as context) |
| `--lang <language>` | Yes | Target: `java`, `typescript`, `go`, `rust`, etc. |

**What it does:**
1. Scans the docs project for feature specs
2. Analyzes reference implementation's architecture decisions (from its planning artifacts)
3. Displays feature list — user selects which to port
4. Confirms target tech stack once (applied to all features)
5. Creates target project skeleton (build file, `.gitignore`, `README.md`, `.code-forge.json`)
6. Batch-generates plans for each selected feature (serial, in dependency order)
7. Generates project-level `planning/overview.md`

**Feature specs stay in the docs project** — accessed via relative paths in `.code-forge.json`, not copied to the target.

**After port completes**, the target is a standard code-forge project:
```bash
cd ../apcore-java
/code-forge:status                    # View all features
/code-forge:impl schema-system        # Start implementing
```

**Resumable:** Re-running port skips features that already have plans.

---

## Features

### Core Advantages

1. **Standardized file organization** — Git-friendly and team-visible
2. **Status tracking** — Track task progress (`pending` → `in_progress` → `completed`)
3. **Pause/resume** — Stop anytime, continue later
4. **TDD-first** — Every task follows test → implement → verify
5. **Deep decomposition** — From documentation to concrete implementation steps
6. **Prompt support** — Start from a text requirement, no document needed
7. **Directory browsing** — Point at a directory, pick a feature to plan
8. **Upstream trace-back** — Bug fixes update plans and docs to stay in sync
9. **Code review** — Structured quality gates before merge
10. **Cross-language porting** — Port a project to a new language with batch planning

## Quick Start

### Scenario 1: New Project with Feature Specs

```bash
# 1. Generate feature spec (via spec-forge)
/spec-forge:feature user-auth

# 2. Generate implementation plan
/code-forge:plan @docs/features/user-auth.md

# 3. Execute tasks
/code-forge:impl user-auth

# 4. Review code
/code-forge:review user-auth
```

### Scenario 2: Quick Idea to Implementation

```bash
# No document needed — describe what you want
/code-forge:plan "Add dark mode support with theme switching and persistence"

# Execute the generated plan
/code-forge:impl dark-mode
```

### Scenario 3: Joining an Existing Project

```bash
# Fix a bug — no prior setup needed
/code-forge:fixbug "Login returns 500 when email contains special characters"

# Add a feature — plan from a prompt
/code-forge:plan "Add CSV export to the user reports page"
/code-forge:impl csv-export

# Optional: configure reference docs for better context
# Create .code-forge.json with reference_docs pointing to project docs
```

### Scenario 4: External Documentation Project

```bash
# Feature specs live in a separate repo
/code-forge:plan @../../docs-project/docs/features/

# Or point directly to a file in another project
/code-forge:plan @../apcore/docs/features/schema-system.md
```

### Scenario 5: Port to Another Language

```bash
# Port all features from a docs project to Java
/code-forge:port @../apcore --ref apcore-python --lang java

# Then implement in the new project
cd ../apcore-java
/code-forge:impl schema-system
```

### Scenario 6: Team Collaboration

```bash
# Developer A: Generate plan, commit to Git
/code-forge:plan @docs/features/big-feature.md
git add planning/ && git commit -m "plan: big-feature"

# Developer B: Pull and execute tasks
git pull
/code-forge:impl big-feature

# Developer C: Review completed work
/code-forge:review big-feature
```

### Scenario 7: Pause/Resume

```bash
# Day 1: Start working
/code-forge:impl user-auth    # Complete 2 tasks, pause

# Day 2: Resume
/code-forge:impl user-auth    # Auto-detects progress, continues from task 3
```

## Generated Structure

```
planning/user-auth/
├── overview.md            # Feature overview + task execution order
├── plan.md                # Architecture design + task dependency graph
├── tasks/                 # Task breakdown
│   ├── setup.md
│   ├── models.md
│   ├── auth-logic.md
│   └── api-endpoints.md
└── state.json             # Status tracking (includes review summary)
```

## File Organization Standard

### Recommended Structure

```
project/
├── docs/                            # Project documentation
│   ├── features/                    # Input: feature specs (owned by spec-forge)
│   │   ├── user-auth.md
│   │   └── payment-gateway.md
│   ├── api/
│   └── guides/
│
├── planning/                        # Output: implementation plans (owned by code-forge)
│   ├── overview.md                  # Project-level overview (auto-generated)
│   ├── user-auth/
│   │   ├── overview.md
│   │   ├── plan.md
│   │   ├── tasks/
│   │   │   ├── setup.md
│   │   │   ├── models.md
│   │   │   └── ...
│   │   └── state.json
│   │
│   └── payment-gateway/
│       ├── overview.md
│       └── ...
│
├── src/                             # Source code
├── tests/                           # Test code
├── .code-forge.json                 # Code Forge configuration (commit to Git)
└── .gitignore
```

### Customizable Directories

```json
// .code-forge.json
{
  "directories": {
    "base": "",
    "input": "docs/features/",
    "output": "planning/"
  }
}
```

See: [CONFIGURATION.md](./docs/CONFIGURATION.md)

### Naming Conventions

- **Feature directories**: kebab-case (`user-auth`, `payment-gateway`)
- **Task files**: descriptive names without numeric prefixes (`setup.md`, `models.md` — not `01-setup.md`)
- **Execution order**: controlled by `overview.md` Task Execution Order table and `state.json`, not by filenames
- **No tool traces**: No "claude-" or "forge-" prefix
- **Git friendly**: All files are suitable for commit

## Configuration

### .code-forge.json

```json
{
  "directories": {
    "base": "",
    "input": "docs/features/",
    "output": "planning/"
  },
  "reference_docs": {
    "sources": ["docs/**/*.md", "README.md"],
    "exclude": ["planning/**"]
  },
  "execution": {
    "default_mode": "ask",
    "auto_tdd": true,
    "task_granularity": "medium"
  },
  "git": {
    "auto_commit": false,
    "commit_state_file": true
  }
}
```

**Three-layer merge:** system defaults → `~/.code-forge.json` (global) → `.code-forge.json` (project). Project config wins.

See: [CONFIGURATION.md](./docs/CONFIGURATION.md)

## Status Tracking

### state.json

```json
{
  "feature": "user-auth",
  "created": "2025-02-13T10:00:00Z",
  "updated": "2025-02-13T15:30:00Z",
  "status": "in_progress",
  "execution_order": ["setup", "models", "auth-logic", "api-endpoints"],
  "progress": {
    "total_tasks": 4,
    "completed": 2,
    "in_progress": 1,
    "pending": 1
  },
  "tasks": [
    {
      "id": "setup",
      "title": "Project Setup",
      "status": "completed",
      "started_at": "2025-02-13T10:00:00Z",
      "completed_at": "2025-02-13T11:00:00Z",
      "assignee": null,
      "commits": ["abc123"]
    }
  ],
  "metadata": {
    "source_doc": "docs/features/user-auth.md",
    "created_by": "code-forge",
    "version": "1.0"
  }
}
```

### Status Definitions

- `pending` — Waiting to execute
- `in_progress` — Currently executing
- `completed` — Finished
- `blocked` — Blocked by dependencies
- `skipped` — Skipped

## Working with spec-forge

```bash
# Full chain: spec → plan → implement → review
/spec-forge:feature user-auth          # Generate feature spec
/code-forge:plan @docs/features/user-auth.md   # Generate plan
/code-forge:impl user-auth             # Execute tasks
/code-forge:review user-auth           # Review code
```

For formal projects, use the full spec-forge chain first:
```bash
/spec-forge:spec-forge user-auth       # PRD → SRS → Tech Design → Test Plan
/spec-forge:feature user-auth          # Extract feature spec from tech design
/code-forge:plan @docs/features/user-auth.md
```

## FAQ

### Q: Must I use TDD?

Recommended but not mandatory. When generating a plan, you can choose testing strategy:
- Strict TDD (recommended)
- Tests after
- Minimal testing

### Q: Can I modify the generated plan?

Yes! After generation you can edit task files, adjust task order, add/delete tasks, and manually update state.json.

### Q: Should `.code-forge.json` be committed?

Yes! It ensures team members use the same directory structure. The `_tool` section tells new members where to install the tool.

### Q: Can I use code-forge on an existing project without prior setup?

Yes! `/code-forge:plan "description"` and `/code-forge:fixbug "description"` work on any project immediately. Optionally configure `.code-forge.json` with `reference_docs` for better context.

### Q: Can the feature spec be in a different project?

Yes! Use a directory or file path: `/code-forge:plan @../../other-project/docs/features/feature.md`. Or configure `directories.input` in `.code-forge.json` to point to an external path.

### Q: How to pause/resume?

Auto-supported. Stop anytime — `state.json` records current state. Run `/code-forge:impl {feature}` to resume.

### Q: Can I customize file locations?

Yes! See [CONFIGURATION.md](./docs/CONFIGURATION.md) for full details.

## Examples

Complete examples in `examples/` directory:
- `examples/user-auth/` — User authentication feature

## License

MIT License
