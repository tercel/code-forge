# Code Forge

> Transform documentation into actionable development plans with status tracking

Combining the **comprehensive depth of deep-\*** with the **standardization of superpowers**, Code Forge transforms documentation into executable development plans.

## Features

### ✅ Combining Best of Both Worlds

| Feature | deep-* | superpowers | **Code Forge** |
|---------|--------|-------------|----------------|
| **Depth Planning** | ✅ Comprehensive Analysis | ⚠️ Basic | ✅ **Comprehensive + TDD** |
| **Task Breakdown** | ✅ Detailed | ⚠️ Manual | ✅ **Auto Breakdown** |
| **File Organization** | ❌ Messy | ✅ `docs/plans/` | ✅ **Structured** |
| **Naming Convention** | ❌ `claude-*` | ✅ Date prefix | ✅ **Feature name** |
| **Status Tracking** | ❌ None | ❌ None | ✅ **JSON Tracking** |
| **Git Friendly** | ❌ | ✅ | ✅ **Team Collaboration** |
| **File Count** | ❌ 20-30+ | ✅ 1-2 | ✅ **5-10 Structured** |

### 🎯 Core Advantages

1. **Standardized file organization** - Git-friendly and team-visible
2. **Status tracking** - Track task progress (pending/in_progress/completed)
3. **Iteration support** - Pause/resume anytime
4. **TDD-first** - Every task is test-driven
5. **Deep decomposition** - From documentation to concrete implementation steps

## Quick Start

### 1. Prepare Documentation

Create feature documentation (or use existing):

```markdown
<!-- docs/features/user-auth.md -->
# User Authentication System

## Requirements
Implement JWT-based user authentication system

## Features
- User registration
- User login
- Token refresh
- Encrypted password storage

## Technical Requirements
- Web framework with REST API support
- Relational database
- bcrypt password hashing
- JWT token authentication
```

### 2. Run Forge

```bash
/forge @docs/features/user-auth.md
```

### 3. Generated Structure

```
docs/implementation/features/user-auth/
├── overview.md            # Feature overview + task execution order
├── plan.md                # Overall implementation plan
├── tasks/                 # Task breakdown
│   ├── setup.md
│   ├── models.md
│   ├── auth-logic.md
│   └── api-endpoints.md
└── state.json             # Status tracking
```

### 4. Execute Tasks

Forge will ask how to proceed:
- **Execute now** - Execute tasks one by one in current session
- **Execute later** - Save plan, implement manually
- **Team collaboration** - Assign tasks to team members

### 5. Track Progress

```json
// state.json
{
  "feature": "user-auth",
  "status": "in_progress",
  "execution_order": ["setup", "models", "auth-logic", "api-endpoints"],
  "progress": {
    "total_tasks": 4,
    "completed": 2,
    "in_progress": 1,
    "pending": 1
  },
  "tasks": [
    {"id": "setup", "status": "completed"},
    {"id": "models", "status": "completed"},
    {"id": "auth-logic", "status": "in_progress"},
    {"id": "api-endpoints", "status": "pending"}
  ]
}
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
│       ├── user-auth/
│       │   ├── overview.md
│       │   ├── plan.md
│       │   ├── tasks/
│       │   │   ├── setup.md
│       │   │   ├── models.md
│       │   │   └── ...
│       │   └── state.json
│       │
│       └── payment-gateway/
│           ├── overview.md
│           └── ...
│
├── src/                             # Source code
├── tests/                           # Test code
├── .code-forge.json                 # Code Forge configuration (optional)
└── .gitignore
```

### Customizable Directories

**Avoid conflict with existing `docs/`?** Use configuration file to customize directories:

```json
// .code-forge.json
{
  "directories": {
    "base": "planning/",           // Default, recommended
    "input": "features/",
    "output": "implementation/"
  }
}
```

See: [CONFIGURATION.md](./CONFIGURATION.md)

### Naming Conventions

- **Feature directories**: kebab-case (`user-auth`, `payment-gateway`)
- **Task files**: `{description}.md` (`setup.md`)
- **No tool traces**: No "claude-" or "forge-" prefix
- **Git friendly**: All files are suitable for commit

## Use Cases

### Scenario 1: New Feature Development

```bash
# 1. Write requirement documentation
vim docs/features/new-feature.md

# 2. Generate implementation plan
/forge @docs/features/new-feature.md

# 3. Execute tasks
# Forge will guide you through them one by one
```

### Scenario 2: Refactor Existing Code

```bash
# 1. Write refactoring plan document
vim docs/features/refactor-auth.md

# 2. Generate task breakdown
/forge @docs/features/refactor-auth.md

# 3. Refactor by task
# Each task is independent and testable
```

### Scenario 3: Team Collaboration

```bash
# Developer A
/forge @docs/features/big-feature.md
# Generate plan, commit to Git

# Developer B
git pull
# Assign task (modify state.json assignee)
# Execute task, update status

# Developer C
git pull
# See progress, assign other tasks
```

### Scenario 4: Pause/Resume

```bash
# Day 1
/forge @docs/features/feature-x.md
# Complete 2 tasks, pause

# Day 2
/forge @docs/features/feature-x.md
# Auto-detect progress, continue execution
```

## Task File Example

Each task file contains:

```markdown
# Task: Project Setup

## Objective
Set up project structure and dependencies

## Files Involved
- Create: project dependency manifest
- Create: test configuration
- Modify: `.gitignore`

## Implementation Steps

### 1. Write tests
```
# Write a test that verifies core dependencies can be imported
# The test should fail initially before dependencies are installed
```

### 2. Run tests (should fail)
```bash
# Run tests using your test runner
# Expected: dependencies not found
```

### 3. Install dependencies
```bash
# Install dependencies using your package manager
```

### 4. Verify tests pass
```bash
# Run tests using your test runner
# Expected: PASSED
```

### 5. Commit
```bash
git add requirements.txt tests/
git commit -m "chore: setup project dependencies"
```

## Acceptance Criteria
- [ ] Dependencies installed successfully
- [ ] Tests pass
- [ ] Git commit completed
```

## Status Tracking

### state.json Explained

```json
{
  "feature": "user-auth",
  "created": "2025-02-13T10:00:00Z",
  "updated": "2025-02-13T15:30:00Z",
  "status": "in_progress",          // Overall status
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
      "assignee": null,              // Can assign in team collaboration
      "commits": ["abc123"]          // Related commit IDs
    },
    {
      "id": "models",
      "title": "Data Models",
      "status": "in_progress",
      "started_at": "2025-02-13T11:30:00Z",
      "completed_at": null,
      "assignee": "developer-a",
      "commits": []
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

- `pending` - Waiting to execute
- `in_progress` - Currently executing
- `completed` - Finished
- `blocked` - Blocked by dependencies
- `skipped` - Skipped

## Git Workflow

### Recommended Commit Strategy

```bash
# 1. Commit planning files
git add docs/implementation/features/xxx/
git commit -m "docs: add implementation plan for xxx"

# 2. Execute tasks, commit individually
git add src/ tests/
git commit -m "feat(xxx): implement setup task"

# 3. Update status (optional)
git add docs/implementation/features/xxx/state.json
git commit -m "docs: update xxx implementation status"
```

### .gitignore Options

If you don't want to commit status files:

```gitignore
# .gitignore
docs/implementation/**/state.json
```

If you don't want to commit the entire implementation directory:

```gitignore
# .gitignore
docs/implementation/
```

## Working with Other Skills

### Complete Workflow

```bash
# 1. Brainstorming design
/brainstorming
# → Generate docs/features/xxx-design.md

# 2. Generate implementation plan
/forge @docs/features/xxx-design.md
# → Generate task breakdown

# 3. Execute tasks (auto-use TDD)
# Forge automatically calls /test-driven-development

# 4. Code review
/requesting-code-review

# 5. Complete branch
/finishing-a-development-branch
```

## Comparison with Other Solutions

### vs deep-plan

| Feature | deep-plan | Code Forge |
|---------|-----------|------------|
| File location | ❌ User specified (scattered) | ✅ `docs/implementation/` |
| Naming | ❌ `claude-*.md` | ✅ No tool traces |
| File count | ❌ 20-30+ | ✅ 5-10 |
| Status tracking | ❌ None | ✅ `state.json` |
| Git friendly | ❌ Unclear | ✅ Designed to commit |
| External API | ⚠️ Optional (Gemini/OpenAI) | ✅ No external dependencies |

### vs superpowers/writing-plans

| Feature | writing-plans | Code Forge |
|---------|---------------|------------|
| Task breakdown | ⚠️ Manual | ✅ Auto-generated |
| Status tracking | ❌ None | ✅ `state.json` |
| Execution support | ⚠️ Manual needed | ✅ Guided execution |
| File count | ✅ 1-2 | ✅ 5-10 (structured) |
| Depth | ⚠️ Basic | ✅ Deep + TDD |

## FAQ

### Q: Must I use TDD?

A: Recommended but not mandatory. When generating plan, you can choose testing strategy:
- Strict TDD (recommended)
- Tests after
- Minimal testing

### Q: Can I modify the generated plan?

A: Of course! After generation you can:
- Edit task files
- Adjust task order
- Add/delete tasks
- Manually update state.json

### Q: Does it support multi-person collaboration?

A: Yes! Through `state.json` `assignee` field:
1. Assign task (set assignee)
2. Update status
3. Commit to Git
4. Team members sync

### Q: Should state.json be committed?

A: Recommended to commit, reasons:
- Team can see progress
- History is traceable
- Facilitates collaboration

If frequent changes bother you, can .gitignore it.

### Q: How to pause/resume?

A: Auto-supported:
- Stop execution anytime
- `state.json` records current state
- Next run `/forge @{feature}` auto-resumes

### Q: Can I customize file locations?

A: Currently fixed at `docs/implementation/features/`, keeping conventions unified.
For special needs, can modify skill configuration.

## Examples

Complete examples in `examples/` directory:
- `examples/user-auth/` - User authentication feature
- `examples/file-upload/` - File upload feature
- `examples/payment/` - Payment system integration

## Contributing

Welcome to contribute improvements!

## License

MIT License
