# Code Forge File Organization Specification

## Default Directory Structure

```
project-root/
├── docs/                            # Existing project documentation (no conflict)
│   ├── api/
│   └── guides/
│
├── planning/                        # Code Forge working directory (default)
│   ├── features/                    # Input: feature documents
│   │   ├── user-auth.md
│   │   └── payment.md
│   │
│   └── implementation/              # Output: implementation plans
│       └── user-auth/
│           ├── overview.md           # Feature overview + task execution order
│           ├── plan.md              # Overall implementation plan
│           ├── tasks/               # Task breakdown
│           │   ├── setup.md
│           │   ├── models.md
│           │   ├── api.md
│           │   └── tests.md
│           └── state.json           # Development status tracking
│
├── .code-forge.json                 # Code Forge configuration (optional)
└── .gitignore
```

## Customizable Directory Structure

Customize directory locations through `.code-forge.json` to avoid conflicts with existing projects.

### Example 1: Using a docs subdirectory

```json
// .code-forge.json
{
  "directories": {
    "base": "docs/",
    "input": "specs/",
    "output": "implementation/"
  }
}
```

**Result:**
```
project/
└── docs/
    ├── api/              # Existing documentation
    ├── specs/            # Forge input
    └── implementation/   # Forge output
```

### Example 2: Fully customized

```json
// .code-forge.json
{
  "directories": {
    "base": "dev/",
    "input": "requirements/",
    "output": "tasks/"
  }
}
```

**Result:**
```
project/
└── dev/
    ├── requirements/     # Forge input
    └── tasks/            # Forge output
```

See: [CONFIGURATION.md](./CONFIGURATION.md)

## Naming Conventions

### Feature directory naming
- Use kebab-case (lowercase + hyphens)
- Concise and descriptive
- Examples: `user-auth`, `payment-gateway`, `file-upload`

### Task file naming
- Format: `{short-description}.md`
- Examples: `setup.md`, `models.md`, `api-endpoints.md`

### State file
- Fixed name: `state.json`
- Optionally commit to Git (recommended for team collaboration)

### Execution order
- Defined in `overview.md` Task Execution Order table
- Also tracked in `state.json` `execution_order` array

## File Content Specification

### overview.md
```markdown
# {Feature Name}

## Overview
Brief description of the feature's purpose and value

## Scope
Clear definition of what is included and excluded

## Task Execution Order
| # | Task File | Description | Status |
|---|-----------|-------------|--------|
| 1 | [setup.md](./tasks/setup.md) | Project setup | ⏸️ Pending |
| 2 | [models.md](./tasks/models.md) | Data models | ⏸️ Pending |

## Dependencies
- Technical dependencies
- Other feature dependencies

## Reference Documents
- [Requirements](../features/xxx.md)
- [Design Documents](../designs/xxx.md)
```

### plan.md
```markdown
# {Feature Name} Implementation Plan

## Goal
[One-sentence description of the goal]

## Architecture Design
[2-3 paragraphs describing the technical solution]

## Technology Stack
- Language/framework
- Key libraries
- Tools

## Task Breakdown
- [ ] setup - Project setup
- [ ] models - Data models
- [ ] api - API implementation
- [ ] tests - Testing

## Risks and Considerations
- Potential risks
- Technical challenges
- Performance considerations

## Acceptance Criteria
- [ ] All tests pass
- [ ] Code review approved
- [ ] Documentation complete
```

### tasks/{name}.md
```markdown
# Task: {Name}

## Goal
[Describe what this task should accomplish]

## Involved Files
- Create: `src/path/to/new_file`
- Modify: `src/path/to/existing`
- Test: `tests/path/to/test_file`

## Implementation Steps

### 1. Write tests
```
# Write tests that verify the expected behavior
# Tests should fail initially before implementation
```

### 2. Run tests (should fail)
```bash
# Run tests using your test runner
# Expected: FAIL
```

### 3. Implement functionality
```
# Implement the functionality to make the tests pass
```

### 4. Verify tests pass
```bash
# Run tests using your test runner
# Expected: PASS
```

### 5. Commit
```bash
git add ...
git commit -m "feat(scope): description"
```

## Dependencies
- Depends on task: [setup]
- Required by: [tests]

## Acceptance Criteria
- [ ] Tests pass
- [ ] Code meets standards
- [ ] Documentation updated
```

### state.json
```json
{
  "feature": "user-auth",
  "created": "2025-02-13T10:00:00Z",
  "updated": "2025-02-13T15:30:00Z",
  "status": "in_progress",
  "execution_order": ["setup", "models", "api", "tests"],
  "progress": {
    "total_tasks": 4,
    "completed": 1,
    "in_progress": 1,
    "pending": 2
  },
  "tasks": [
    {
      "id": "setup",
      "title": "Project setup and dependencies",
      "status": "completed",
      "started_at": "2025-02-13T10:00:00Z",
      "completed_at": "2025-02-13T11:00:00Z",
      "assignee": null,
      "commits": ["abc123"]
    },
    {
      "id": "models",
      "title": "Data model implementation",
      "status": "in_progress",
      "started_at": "2025-02-13T11:30:00Z",
      "completed_at": null,
      "assignee": null,
      "commits": []
    },
    {
      "id": "api",
      "title": "API endpoint implementation",
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "assignee": null,
      "commits": []
    },
    {
      "id": "tests",
      "title": "Integration testing",
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "assignee": null,
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

## Git Commit Recommendations

### Recommended commits
- ✅ All files under `docs/implementation/`
- ✅ `state.json` (team visibility of progress)

### Optional commits
- ⚠️ `state.json` can be added to .gitignore if it changes frequently

### .gitignore example
```gitignore
# If you don't want to commit status files
docs/implementation/**/state.json

# If you don't want to commit the entire implementation directory
docs/implementation/
```

## Comparison with Existing Systems

| Feature | deep-* | superpowers | Code Forge |
|---------|--------|-------------|------------|
| File location | ❌ Scattered | ✅ `docs/plans/` | ✅ `docs/implementation/` |
| Naming convention | ❌ `claude-*` | ✅ Date prefix | ✅ Feature name + task sequence |
| File count | ❌ 20-30+ | ✅ 1-2 | ✅ 5-10 (structured) |
| Status tracking | ❌ None | ❌ None | ✅ state.json |
| Git friendly | ❌ | ✅ | ✅ |
| Team collaboration | ❌ | ✅ | ✅ |
| Deep planning | ✅ | ⚠️ | ✅ |
| Task breakdown | ✅ | ⚠️ | ✅ |
