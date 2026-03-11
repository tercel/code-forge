# Task: User Models and Database

## Goal

Define the User data model, request/response schemas, and database configuration.

## Files Involved

- Create: src/auth/models (User model with id, email, hashed_password, created_at)
- Create: src/auth/schemas (registration, login, and user response schemas)
- Create: database configuration (connection, session management)
- Create: tests/auth/test_models (model and schema tests)

## Steps

### 1. Write tests

```
# tests/auth/test_models
# Verify that:
# - User model has required fields (id, email, hashed_password, created_at)
# - Email uniqueness constraint exists
# - Registration schema validates email format and password length
# - Login schema requires email and password
# - User response schema excludes hashed_password
```

### 2. Run tests (should fail)

```bash
# Expected: model/schema not found errors
```

### 3. Create database configuration

- Connection string from environment variable
- Session factory with proper lifecycle
- Base model class for all entities

### 4. Create User model

```
# src/auth/models
# Fields:
#   - id: primary key (UUID or auto-increment)
#   - email: unique, indexed, not null
#   - hashed_password: string, not null
#   - is_active: boolean, default true
#   - created_at: timestamp, auto-set
```

### 5. Create request/response schemas

- Registration: email (validated format) + password (min length)
- Login: email + password
- User response: id, email, is_active, created_at (no password)
- Token response: access_token, token_type

### 6. Run tests (should pass)

```bash
# All model and schema tests should pass
```

### 7. Commit

```bash
git add .
git commit -m "feat(auth): add user model and schemas

- Define User model with email uniqueness constraint
- Add registration, login, and response schemas
- Configure database connection and session management
- Add model and schema tests
"
```

## Acceptance Criteria

- [ ] User model defined with all required fields
- [ ] Email uniqueness enforced at database level
- [ ] Registration schema validates email format and password length
- [ ] User response schema excludes sensitive fields
- [ ] Database connects successfully
- [ ] All tests pass

## Dependencies

- **Depends on**: setup
- **Required by**: auth-logic, api

## Estimated Time

2-3 hours
