# User Authentication System

## Overview

Implement a JWT-based user authentication system that supports registration, login, and token refresh.

## Scope

**Included:**
- User registration (email + password)
- User login (returns JWT token)
- Token refresh (extend session)
- Get current user info
- Password hashing (bcrypt or equivalent)
- JWT authentication

**Excluded:**
- Social login (OAuth)
- Two-factor authentication (2FA)
- Password reset
- User permission management
- Email verification

## Tech Stack

- **Backend**: Web framework with routing and middleware support
- **Database**: Relational database + ORM
- **Authentication**: JWT, bcrypt (or equivalent)
- **Testing**: Unit testing framework with coverage

## Task Execution Order

| # | Task File | Description | Status |
|---|-----------|-------------|--------|
| 1 | [setup.md](./tasks/setup.md) | Project setup and dependencies | ⏸️ Pending |
| 2 | [models.md](./tasks/models.md) | User models and database | ⏸️ Pending |
| 3 | [auth-logic.md](./tasks/auth-logic.md) | Authentication logic implementation | ⏸️ Pending |
| 4 | [api.md](./tasks/api.md) | API endpoints implementation | ⏸️ Pending |

## Progress

- **Total tasks**: 4
- **Completed**: 0
- **In progress**: 0
- **Pending**: 4

## References

- [Source requirements](../input/user-auth.md)
- [Implementation plan](./plan.md)

## Quick Start

### 1. View the plan
```bash
cat plan.md
```

### 2. Execute tasks
Run the task files in `tasks/` following the execution order above.

### 3. Track progress
Check `state.json` for the current status.
