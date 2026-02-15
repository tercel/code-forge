# Code Forge

> Transform documentation into actionable development plans with status tracking

Combining the **comprehensive depth of deep-\*** with the **standardization of superpowers**, Code Forge transforms documentation into executable development plans.

## Commands

| Command | Description |
|---------|------------|
| `/code-forge:status` | Dashboard — show all features and progress |
| `/code-forge:plan @doc.md` | Generate plan from a feature document |
| `/code-forge:plan "requirement"` | Generate plan from a text prompt |
| `/code-forge:impl [feature]` | Execute pending tasks for a feature |
| `/code-forge:status [feature]` | View dashboard or feature detail |
| `/code-forge:fixbug "description"` | Debug and fix a bug with upstream trace-back |
| `/code-forge:review [feature]` | Review code quality for a feature |

Each subcommand is a standalone slash command — invoke directly without a router.

### Subcommand Details

- **plan** — Analyzes a feature document (or text prompt), generates an implementation plan with architecture design, task breakdown, and TDD steps. Supports prompt-to-document: `/code-forge:plan "implement user login"` auto-creates a feature doc then plans.
- **impl** — Executes pending tasks for a feature using isolated sub-agents. Supports pause/resume, parallel execution, and progress tracking via `state.json`.
- **status** — Displays a project dashboard (all features) or detailed progress for a single feature. Regenerates the project-level overview.
- **fixbug** — Systematically debugs bugs with root cause diagnosis at 4 levels (code → task → plan → requirements). Interactively confirms upstream document updates to keep docs in sync.
- **review** — Reviews completed feature code across 4 dimensions: code quality, test coverage, security (OWASP top 10), and plan consistency. Generates a review report.

## Features

### Combining Best of Both Worlds

| Feature | deep-* | superpowers | **Code Forge** |
|---------|--------|-------------|----------------|
| **Depth Planning** | Comprehensive Analysis | Basic | **Comprehensive + TDD** |
| **Task Breakdown** | Detailed | Manual | **Auto Breakdown** |
| **File Organization** | Messy | `docs/plans/` | **Structured** |
| **Naming Convention** | `claude-*` | Date prefix | **Feature name** |
| **Status Tracking** | None | None | **JSON Tracking** |
| **Git Friendly** | No | Yes | **Team Collaboration** |
| **Bug Debugging** | None | Basic | **Upstream Trace-back** |
| **Code Review** | None | Manual | **Multi-dimension Review** |

### Core Advantages

1. **Standardized file organization** - Git-friendly and team-visible
2. **Status tracking** - Track task progress (pending/in_progress/completed)
3. **Iteration support** - Pause/resume anytime
4. **TDD-first** - Every task is test-driven
5. **Deep decomposition** - From documentation to concrete implementation steps
6. **Prompt support** - Start from a text requirement, no document needed
7. **Upstream trace-back** - Bug fixes can update plans and docs to stay in sync
8. **Code review** - Structured quality gates before merge

## Quick Start

### From a Document

```bash
# 1. Write feature documentation
vim planning/features/user-auth.md

# 2. Generate implementation plan
/code-forge:plan @planning/features/user-auth.md

# 3. Execute tasks
/code-forge:impl user-auth

# 4. Review code
/code-forge:review user-auth
```

### From a Prompt

```bash
# No document needed — just describe what you want
/code-forge:plan "Implement JWT-based user authentication with login, registration, and token refresh"

# Code Forge auto-creates a feature doc, then generates the plan
```

### Generated Structure

```
planning/implementation/user-auth/
├── overview.md            # Feature overview + task execution order
├── plan.md                # Overall implementation plan
├── tasks/                 # Task breakdown
│   ├── setup.md
│   ├── models.md
│   ├── auth-logic.md
│   └── api-endpoints.md
├── state.json             # Status tracking
└── review.md              # Code review report (after /code-forge:review)
```

## File Organization Standard

### Recommended Structure (Default Configuration)

```
project/
├── docs/                            # Existing project documentation (no conflict)
│   ├── api/
│   └── guides/
│
├── planning/                        # Code Forge working directory
│   ├── features/                    # Input: feature documentation
│   │   ├── user-auth.md
│   │   └── payment-gateway.md
│   │
│   └── implementation/              # Output: implementation planning
│       ├── overview.md              # Project-level overview (auto-generated)
│       ├── user-auth/
│       │   ├── overview.md
│       │   ├── plan.md
│       │   ├── tasks/
│       │   │   ├── setup.md
│       │   │   ├── models.md
│       │   │   └── ...
│       │   ├── state.json
│       │   └── review.md
│       │
│       └── payment-gateway/
│           ├── overview.md
│           └── ...
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
    "base": "planning/",
    "input": "features/",
    "output": "implementation/"
  }
}
```

See: [CONFIGURATION.md](./docs/CONFIGURATION.md)

### Naming Conventions

- **Feature directories**: kebab-case (`user-auth`, `payment-gateway`)
- **Task files**: `{description}.md` (`setup.md`)
- **No tool traces**: No "claude-" or "forge-" prefix
- **Git friendly**: All files are suitable for commit

## Use Cases

### New Feature Development

```bash
/code-forge:plan @planning/features/new-feature.md
/code-forge:impl new-feature
/code-forge:review new-feature
```

### Quick Prototyping from Idea

```bash
/code-forge:plan "Add dark mode support with theme switching and persistence"
/code-forge:impl dark-mode
```

### Bug Fixing with Trace-back

```bash
/code-forge:fixbug "Login page returns 500 error when email contains special characters"
# Diagnoses root cause → fixes code → updates upstream docs if needed
```

### Team Collaboration

```bash
# Developer A: Generate plan, commit to Git
/code-forge:plan @planning/features/big-feature.md

# Developer B: Assign and execute tasks
git pull
/code-forge:impl big-feature

# Developer C: Review completed work
/code-forge:review big-feature
```

### Pause/Resume

```bash
# Day 1: Start working
/code-forge:plan @planning/features/feature-x.md
/code-forge:impl feature-x    # Complete 2 tasks, pause

# Day 2: Resume
/code-forge:impl feature-x    # Auto-detects progress, continues
```

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
    "source_doc": "planning/features/user-auth.md",
    "created_by": "code-forge",
    "version": "1.0"
  }
}
```

### Status Definitions

- `pending` - Waiting to execute
- `in_progress` - Currently executing
- `completed` - Finished
- `blocked` - Blocked by dependencies
- `skipped` - Skipped

## Working with Other Skills

```bash
# 1. Brainstorm design
/brainstorming
# → Generate planning/features/xxx-design.md

# 2. Generate implementation plan
/code-forge:plan @planning/features/xxx-design.md

# 3. Execute tasks (auto-uses TDD)
/code-forge:impl xxx

# 4. Review code quality
/code-forge:review xxx

# 5. Complete branch
/finishing-a-development-branch
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

### Q: How to pause/resume?

Auto-supported. Stop anytime — `state.json` records current state. Run `/code-forge:impl {feature}` to resume.

### Q: Can I customize file locations?

Yes! See [CONFIGURATION.md](./docs/CONFIGURATION.md) for full details.

## Examples

Complete examples in `examples/` directory:
- `examples/user-auth/` - User authentication feature

## License

MIT License
