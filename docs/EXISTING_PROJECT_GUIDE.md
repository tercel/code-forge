# Using Code Forge in Existing Projects

> How to use Code Forge in projects that are in progress or already completed

**Applicable scenarios**:
- Project has been in development for a while
- Some features completed, others still in development
- Want to add planning for new features in an existing codebase
- Want to standardize existing development workflows

---

## Quick Start

The simplest way to use Code Forge on an existing project:

```bash
# Describe what you want to build — no docs needed
/code-forge:plan "Add OAuth login with Google and GitHub"

# Or use --tmp to avoid adding plan files to the project
/code-forge:plan --tmp "Add OAuth login with Google and GitHub"

# Execute tasks
/code-forge:impl
```

Code Forge works on any project immediately. No prior setup or configuration is required.

---

## Common Scenarios

### Scenario 1: Adding a New Feature to an Existing Project

**The standard approach.** Describe the new feature and let Code Forge plan it:

```bash
# From a text prompt
/code-forge:plan "Add batch CSV export to user list with date range filter"

# Or write a feature doc first for better plan quality
cat > docs/features/csv-export.md << 'EOF'
# Batch CSV Export

## Requirements
- Export user list to CSV format
- Support date range filtering
- Handle large datasets (pagination/streaming)
- Include all user fields: name, email, role, created_at

## Technical Context
- Existing user list API at GET /api/users
- Using Express + PostgreSQL
- Tests use Jest
EOF

/code-forge:plan @docs/features/csv-export.md
/code-forge:impl csv-export
```

### Scenario 2: Documenting Completed Features

Create a feature doc describing what was built, then plan from it. The generated plan serves as documentation and a reference for future work:

```bash
cat > docs/features/user-auth.md << 'EOF'
# User Authentication (Completed)

## Implemented Features
- User registration: POST /auth/register
- User login: POST /auth/login
- JWT Token verification middleware
- Password encryption (bcrypt)
- Token refresh mechanism

## Technical Implementation
- FastAPI + python-jose (JWT) + PostgreSQL + SQLAlchemy ORM

## Existing Files
- src/auth/models.py - User model
- src/auth/routes.py - Authentication routes
- src/auth/schemas.py - Pydantic schemas
- src/auth/utils.py - JWT utilities
- tests/test_auth.py - Test file
EOF

/code-forge:plan @docs/features/user-auth.md
```

After the plan is generated, manually update `state.json` to mark all tasks as `"completed"`:

```bash
# Edit state.json to reflect actual status
vim planning/user-auth/state.json
# Change each task's "status" from "pending" to "completed"
# Add actual file paths and completion dates
```

**Value:** New team members can quickly understand feature decomposition, and similar features can reuse the plan as a template.

### Scenario 3: Partially Completed Feature

If a feature is partially done and you want to plan the remaining work, describe **only the remaining work** in the feature doc:

```bash
cat > docs/features/auth-enhancement.md << 'EOF'
# Authentication Enhancement

## Context
Basic username/password login and JWT auth already implemented.

## Remaining Work
- OAuth2 third-party login (Google, GitHub)
- Two-factor authentication (2FA) with TOTP
- Fine-grained RBAC permission system
- Session management
EOF

/code-forge:plan @docs/features/auth-enhancement.md
/code-forge:impl auth-enhancement
```

The plan will only cover the remaining work. No need to describe what's already done.

### Scenario 4: Multi-Module Project

For projects with multiple modules at different stages, plan each module separately:

```bash
# Plan only the modules that need work
/code-forge:plan @docs/features/registry.md      # In-progress module
/code-forge:plan @docs/features/decorator.md      # Not-started module

# Check overall status
/code-forge:status

# Execute next pending feature
/code-forge:impl
```

Use `/code-forge:status` to see all features and their progress in one dashboard.

### Scenario 5: Don't Want Plan Files in the Project

Use `--tmp` to keep plan files out of the project directory:

```bash
/code-forge:plan --tmp "Add payment gateway integration"
/code-forge:impl          # Finds plans in .code-forge/tmp/ automatically
/code-forge:finish        # Cleans up tmp files after merge
```

---

## Best Practices

### Recommended

1. **Describe only what needs to be done** — Don't try to document the entire existing codebase. Focus on new or remaining work.

2. **Use `/review --project` first** — If unfamiliar with the codebase, run a project review to understand architecture and conventions before planning.

3. **Process by module** — Large projects should plan each module separately rather than one massive plan.

4. **Use `--tmp` for quick tasks** — If the project doesn't have a `planning/` convention, use temporary mode to avoid clutter.

5. **Commit `.code-forge.json`** — If the team adopts Code Forge, commit the config for consistency.

### Not Recommended

1. **Force-documenting everything** — Don't spend time generating plans for simple, well-understood code.
2. **Over-planning** — A one-line bug fix doesn't need a plan. Use `/code-forge:tdd` or `/code-forge:debug` instead.
3. **Ignoring existing tests** — Code Forge generates TDD tasks. If tests already exist, mention them in the feature doc so the plan builds on them.

---

## FAQ

### Q: What's the value of planning for completed code?

Documentation, knowledge transfer, and template reuse. New team members can quickly understand feature decomposition, and similar features can reference the plan.

### Q: Multi-module project with inter-module dependencies?

Plan each module separately. Use `/code-forge:status` for the project dashboard. Dependencies between modules are tracked in `plan.md` dependency graphs.

### Q: Large project with dozens of features?

Plan selectively. Core and complex features benefit from planning. Simple utilities don't need it.

### Q: Can Code Forge help with refactoring?

Code Forge is a planning tool, not a refactoring tool. But you can create a feature doc describing the desired structure, generate a plan, and execute refactoring as tasks with TDD.

---

**Related documents**:
- [OVERVIEW_GUIDE.md](./OVERVIEW_GUIDE.md) - Multi-module project management
- [README.md](../README.md) - Full command reference and quick start
