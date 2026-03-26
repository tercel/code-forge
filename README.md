# Code Forge

> Complete development workflow — from TDD-driven implementation plans to execution, debugging, code review, git worktree management, branch lifecycle, and parallel agent dispatch.

## Commands

| Command | Description |
|---------|------------|
| **End-to-End** | |
| `/code-forge:build @doc.md` | Full pipeline: test cases → plan → impl → review → verify |
| `/code-forge:build "add feature"` | Same pipeline but derives requirements from prompt + code analysis |
| `/code-forge:build "add tests"` | Test-only mode: test cases → tdd → review → verify |
| **Planning & Execution** | |
| `/code-forge:plan @doc.md` | Generate plan from a feature document |
| `/code-forge:plan @dir/` | Browse a directory and pick a feature to plan |
| `/code-forge:plan "requirement"` | Generate plan from a text prompt |
| `/code-forge:plan --tmp "requirement"` | Generate plan in `.code-forge/tmp/` (no project pollution) |
| `/code-forge:impl [feature]` | Execute pending tasks for a feature |
| `/code-forge:status [feature]` | View dashboard or feature detail |
| **Quality & Debugging** | |
| `/code-forge:review [feature]` | Review code quality for a feature or project |
| `/code-forge:review --feedback` | Evaluate and respond to incoming review comments |
| `/code-forge:review --github-pr` | Post 14-dimension review to a GitHub PR |
| `/code-forge:fix "description"` | Debug and fix a bug with upstream trace-back |
| `/code-forge:fix --review` | Batch-fix all issues from a review report |
| `/code-forge:debug "description"` | Systematic root cause debugging (general-purpose) |
| **Development Methodology** | |
| `/code-forge:tdd` | Enforce Red-Green-Refactor cycle (standalone TDD) |
| `/code-forge:verify` | Verify work before claiming completion |
| **Workspace & Branch Lifecycle** | |
| `/code-forge:worktree <feature>` | Create isolated git worktree with project setup |
| `/code-forge:finish` | Merge, PR, keep, or discard a completed branch |
| **Advanced** | |
| `/code-forge:parallel` | Dispatch parallel agents for independent problems |
| `/code-forge:port @docs --ref impl --lang java` | Port a project to a new language |

Each command is a standalone slash command — invoke directly without a router.

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

# Temporary mode — plan files in .code-forge/tmp/ (auto-gitignored)
/code-forge:plan --tmp "Implement JWT-based user authentication"
/code-forge:plan --tmp @docs/features/user-auth.md
```

**What it does:**
1. Reads and analyzes the feature document (via sub-agent)
2. Asks for tech stack, testing strategy, and task granularity
3. Generates `plan.md` with architecture design + task dependency graph
4. Creates `tasks/*.md` with TDD-first steps, code examples, and acceptance criteria
5. Generates `overview.md` with task execution order table
6. Initializes `state.json` for progress tracking
7. Updates project-level `planning/overview.md` with all features and dependencies

**Directory mode:** Scans for `*.md` files and lets you pick one. Works with external paths.

**Prompt mode:** Auto-delegates to `spec-forge:feature` to generate a feature spec, then plans from that.

**Reference docs:** Configure `reference_docs.sources` in `.code-forge.json` to inject existing project documentation as context.

---

### impl — Execute Tasks

Executes pending tasks for a feature using isolated sub-agents. Each task runs in its own sub-agent to prevent context exhaustion.

```bash
/code-forge:impl user-auth     # Execute a specific feature
/code-forge:impl               # Auto-select next pending/in-progress feature
```

**What it does:**
1. Locates the feature's `state.json`
2. Finds the next pending task respecting dependency order
3. Dispatches a sub-agent to execute: write tests → run → implement → verify → commit
4. After each task, asks: completed / pause / skip
5. Supports parallel execution for independent tasks

**Pause/resume:** Stop anytime. Progress is saved in `state.json`. Re-run to continue where you left off.

---

### status — Project Dashboard

```bash
/code-forge:status             # Global dashboard — all features
/code-forge:status user-auth   # Feature detail — tasks and progress
```

Auto-regenerates `planning/overview.md` on each run.

---

### review — Code Quality Review

Comprehensive 14-dimension code review with four modes.

```bash
/code-forge:review user-auth       # Feature mode — review against plan.md
/code-forge:review --project       # Project mode — review entire project
/code-forge:review --feedback      # Feedback mode — evaluate incoming review comments
/code-forge:review --github-pr     # GitHub PR mode — post review as PR comment
/code-forge:review --github-pr 123 # GitHub PR mode — specific PR number
```

**Review dimensions (14):**

| Tier | Dimensions | Merge Policy |
|------|-----------|--------------|
| Tier 1 — Must-Fix | D1: Functional Correctness, D2: Security, D3: Resource Management | Must fix before merge |
| Tier 2 — Should-Fix | D4: Code Quality, D5: Architecture, D6: Performance, D7: Test Coverage | Should fix |
| Tier 3 — Recommended | D8: Error Handling, D9: Observability, D10: Standards | Recommended |
| Tier 4 — Nice-to-Have | D11: Backward Compat, D12: Maintainability, D13: Dependencies, D14: Accessibility | Track as tech debt |

**Severity levels:** `blocker` > `critical` > `warning` > `suggestion`

**Modes:**
- **Feature mode** — Reviews a feature against its `plan.md` acceptance criteria
- **Project mode** — Reviews entire project against planning docs, upstream docs, or bare
- **Feedback mode** — Evaluates incoming review comments; classifies each as correct/YAGNI/partially correct/incorrect/unclear/style preference; implements valid fixes with TDD
- **GitHub PR mode** — Runs 14-dimension review on a PR diff, filters out suggestions (noise reduction), posts as a single GitHub comment with severity badges and file links

**Output:** Terminal display by default. Use `--save` to persist to disk. GitHub PR mode posts directly to GitHub.

---

### fix — Debug with Upstream Trace-back

For bugs in code-forge tracked features (has `state.json`). Traces root cause across 4 levels and syncs upstream documents.

```bash
/code-forge:fix "Login page returns 500 when email has special characters"
/code-forge:fix @bug-report.md
/code-forge:fix --review user-auth              # Batch-fix all issues from review report
/code-forge:fix --review                        # Auto-detect review report and fix
```

**Root cause levels:**

| Level | Root Cause | Action |
|-------|-----------|--------|
| 1 | Code bug (logic error, boundary miss) | Fix code only |
| 2 | Incomplete task description | Fix code + update task.md |
| 3 | Plan design flaw | Fix code + update plan.md |
| 4 | Incomplete requirements | Fix code + update feature spec |

Works on any project — does not require prior code-forge setup.

---

### debug — Systematic Root Cause Debugging

General-purpose debugging for any bug, test failure, or unexpected behavior. Use when the issue is NOT tracked by code-forge (no `state.json`). For code-forge features, use `fix` instead.

```bash
/code-forge:debug "Tests failing after upgrading React to v19"
/code-forge:debug "Memory leak in WebSocket connection handler"
```

**Four phases:**
1. **Root Cause Investigation** — Read errors, reproduce, check recent changes, trace data flow
2. **Pattern Analysis** — Find working examples, compare, identify differences
3. **Hypothesis Testing** — One hypothesis at a time, minimal change, verify
4. **Implementation** — TDD fix (failing test first, then fix, then full suite)

**Escalation:** After 3 failed fix attempts, STOP — likely wrong architecture or mental model. Discuss with user.

---

### tdd — Standalone TDD Enforcement

Enforces Red-Green-Refactor cycle for any code change outside the code-forge:impl workflow.

```bash
/code-forge:tdd
```

**The cycle:**
1. **RED** — Write a failing test (one behavior, clear name, real code)
2. **VERIFY RED** — Run it, confirm it fails for the right reason
3. **GREEN** — Simplest code that makes the test pass
4. **VERIFY GREEN** — Run it, confirm all tests pass
5. **REFACTOR** — Clean up (all tests stay green)
6. **REPEAT**

**Iron Law:** No production code without a failing test first. No exceptions.

---

### verify — Completion Verification

Evidence-based gate before claiming any work is done. Prevents "should work" statements.

```bash
/code-forge:verify
```

**The gate:** `IDENTIFY → RUN → READ → VERIFY → CLAIM`

1. Identify the verification command (test, build, lint, type-check)
2. Run it fresh (not from memory)
3. Read the complete output
4. Verify output matches the claim
5. Only then make the claim

**Forbidden words:** "should work", "probably", "seems to", "I believe", "based on the changes"

---

### worktree — Git Worktree Management

Creates an isolated git worktree for a feature with automatic project setup.

```bash
/code-forge:worktree user-auth          # New worktree for a feature
/code-forge:worktree hotfix-login       # New worktree for a hotfix
```

**What it does:**
1. Creates a new branch and worktree in `.worktrees/{feature-name}/`
2. Verifies `.gitignore` includes `.worktrees/`
3. Runs project setup (detects npm/pip/cargo/go and installs dependencies)
4. Runs baseline tests to confirm clean starting state
5. Suggests next steps: `code-forge:impl` (tracked) or `code-forge:tdd` (ad-hoc)

---

### finish — Branch Lifecycle

Completes work on the current branch with four options.

```bash
/code-forge:finish
```

**Options:**
1. **Merge to base** — No-fast-forward merge to main/base branch
2. **Create PR** — Push and open a GitHub PR via `gh`
3. **Keep branch** — Push without merging
4. **Discard** — Delete branch and worktree (with confirmation gate)

Auto-detects worktree context. Follows `code-forge:verify` discipline before any merge/PR.

---

### parallel — Parallel Agent Dispatch

Dispatches multiple sub-agents to work on independent problems simultaneously.

```bash
/code-forge:parallel
```

**What it does:**
1. Lists all problems/tasks to parallelize
2. Assesses independence (shared files, data dependencies, execution order)
3. Builds agent prompts with explicit scope boundaries
4. Dispatches up to 5 agents concurrently via Task tool
5. Collects results, resolves conflicts, integrates

**Independence rule:** Only truly independent tasks run in parallel. If tasks share files or have data dependencies, they run sequentially.

---

### port — Cross-Language Porting

Ports a documentation-driven project to a new target language.

```bash
/code-forge:port @../apcore --ref apcore-python --lang java
```

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `@<docs-project>` | Yes | Documentation project with `docs/features/*.md` |
| `--ref <name>` | No | Reference implementation (uses its `planning/` as context) |
| `--lang <language>` | Yes | Target: `java`, `typescript`, `go`, `rust`, etc. |

---

## Quick Start

### Full Workflow: Spec → Plan → Implement → Review

```bash
/spec-forge:feature user-auth                     # Generate feature spec
/code-forge:plan @docs/features/user-auth.md      # Generate plan
/code-forge:impl user-auth                        # Execute tasks (TDD)
/code-forge:review user-auth                      # Review — blockers/criticals?
/code-forge:fix --review                          #   Yes → batch-fix all issues
/code-forge:review user-auth                      #   Re-review after fix
/code-forge:review --github-pr                    # Post review to PR
```

### Quick Idea to Implementation

```bash
/code-forge:plan "Add dark mode support with theme switching"
/code-forge:impl dark-mode
```

### Isolated Feature Development

```bash
/code-forge:worktree user-auth                    # Create worktree + branch
/code-forge:plan @docs/features/user-auth.md      # Plan inside worktree
/code-forge:impl user-auth                        # Implement
/code-forge:review user-auth                      # Review
/code-forge:fix --review                          # Fix issues (if any)
/code-forge:finish                                # Merge or PR
```

### Joining a Project Midway (No Docs)

When you join an existing project to develop a new feature — no design docs, no prior setup — use this minimal flow:

```bash
# Step 1: (Optional) Understand the project first
/code-forge:review --project                      # 14-dimension scan of the codebase

# Step 2: Describe the requirement in plain text — no docs needed
/code-forge:plan "Add batch CSV export to user list with date range filter"

# Step 3: Execute tasks (TDD-driven)
/code-forge:impl

# Step 4: Review and fix
/code-forge:review                                # Check quality
/code-forge:fix --review                          # Fix issues (if any)

# Step 5: Verify and finish
/code-forge:verify
/code-forge:finish
```

**Don't want plan files polluting the project?** Use `--tmp`:

```bash
# Plan files go to .code-forge/tmp/ (auto-gitignored), not planning/
/code-forge:plan --tmp "Add batch CSV export to user list with date range filter"
/code-forge:impl                                  # Automatically finds plans in .code-forge/tmp/
/code-forge:finish                                # Cleans up .code-forge/tmp/ after merge
```

**Key points:**
- `/plan` accepts plain text — formal documents are NOT required
- `/impl` depends on `/plan` — you cannot skip `/plan` and go directly to `/impl`
- Use `--tmp` when the project has no `planning/` convention — plan files are auto-gitignored and cleaned up on finish
- If you want ad-hoc development without task tracking, use `/tdd` instead of `/plan` + `/impl`
- `/review --project` is optional but recommended when you're unfamiliar with the codebase

### Ad-hoc Development (No Tracking)

```bash
/code-forge:worktree hotfix-login                 # Create worktree
/code-forge:tdd                                   # TDD cycle for the fix
/code-forge:verify                                # Verify before claiming done
/code-forge:finish                                # Merge or PR
```

### Bug Investigation

```bash
# Code-forge tracked feature:
/code-forge:fix "Login returns 500 with special chars"

# Batch-fix all issues found by review:
/code-forge:fix --review user-auth
/code-forge:fix --review                          # Auto-detect feature

# General debugging (no state.json):
/code-forge:debug "Memory leak in WebSocket handler"
```

### Team Collaboration

```bash
# Developer A: Generate plan
/code-forge:plan @docs/features/big-feature.md
git add planning/ && git commit -m "plan: big-feature"

# Developer B: Implement
git pull
/code-forge:impl big-feature

# Developer C: Review and post to PR
/code-forge:review big-feature                    # Local review
/code-forge:fix --review                          # Fix issues found by review
/code-forge:review --github-pr                    # Post review to PR

# Developer B: Handle feedback
/code-forge:review --feedback                     # Evaluate and respond
```

### Parallel Problem Solving

```bash
/code-forge:parallel    # Describe problems, agents work concurrently
```

---

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

```
project/
├── docs/                            # Project documentation
│   └── features/                    # Input: feature specs (owned by spec-forge)
│
├── planning/                        # Output: implementation plans (owned by code-forge)
│   ├── overview.md                  # Project-level overview (auto-generated)
│   └── user-auth/
│       ├── overview.md
│       ├── plan.md
│       ├── tasks/
│       └── state.json
│
├── .worktrees/                      # Git worktrees (auto-managed, gitignored)
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

## FAQ

### Q: Must I use TDD?

Recommended but not mandatory. When generating a plan, you can choose testing strategy: Strict TDD (recommended), Tests after, or Minimal testing.

### Q: Can I modify the generated plan?

Yes. Edit task files, adjust task order, add/delete tasks, and manually update state.json.

### Q: Should `.code-forge.json` be committed?

Yes. It ensures team members use the same directory structure.

### Q: Can I use code-forge on an existing project without prior setup?

Yes. `/code-forge:plan "description"` and `/code-forge:fix "description"` work on any project immediately. `/code-forge:tdd`, `/code-forge:debug`, and `/code-forge:verify` also work standalone.

### Q: Can the feature spec be in a different project?

Yes. Use a path: `/code-forge:plan @../../other-project/docs/features/feature.md`.

### Q: How to pause/resume?

Auto-supported. Stop anytime — `state.json` records current state. Run `/code-forge:impl` to resume.

### Q: When should I use `debug` vs `fix`?

Use `/code-forge:fix` when the bug is in a code-forge tracked feature (has `state.json`) — it traces root cause across 4 levels and syncs upstream documents. Use `/code-forge:debug` for general-purpose debugging on any codebase.

### Q: Can I skip `/plan` and go directly to `/impl` with a requirement description?

No. `/impl` executes tasks from an existing plan (`state.json`). Without `/plan`, there are no tasks to execute. The minimum flow is `/plan` → `/impl`. If you want a single-command experience without tracking, use `/code-forge:tdd` instead.

### Q: I don't want plan files cluttering the project. Can I avoid them?

Yes. Use `--tmp`: `/code-forge:plan --tmp "requirement"`. Plan files are written to `.code-forge/tmp/` which is auto-gitignored. `/impl` and `/status` automatically search this location. `/finish` cleans up tmp files after merge or discard.

### Q: When should I use `tdd` vs `impl`?

Use `/code-forge:impl` for planned features with task breakdown. Use `/code-forge:tdd` for ad-hoc development, quick fixes, or any code change not tracked by code-forge.

### Q: How does `--github-pr` differ from local review?

Local review (`/code-forge:review [feature]`) shows all findings including suggestions in the terminal. GitHub PR mode (`--github-pr`) filters out suggestions to reduce noise and posts only warnings and above as a GitHub comment with file links.

## License

MIT License
