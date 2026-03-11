# Task: API Endpoints Implementation

## Goal

Implement REST API endpoints for registration, login, token refresh, and current user retrieval.

## Files Involved

- Create: src/auth/routes (API endpoint definitions)
- Update: app entry point (mount auth routes)
- Create: tests/auth/test_api (integration tests)

## Steps

### 1. Write integration tests

```
# tests/auth/test_api
# Verify that:
# - POST /auth/register with valid data returns 201 + user info
# - POST /auth/register with duplicate email returns 409
# - POST /auth/register with invalid email returns 422
# - POST /auth/login with correct credentials returns 200 + token
# - POST /auth/login with wrong password returns 401
# - POST /auth/login with non-existent user returns 401
# - GET /auth/me with valid token returns current user
# - GET /auth/me without token returns 401
# - GET /auth/me with expired token returns 401
# - POST /auth/refresh with valid token returns new token
```

### 2. Run tests (should fail)

```bash
# Expected: route not found / 404 errors
```

### 3. Implement registration endpoint

```
# POST /auth/register
# Input: email, password (via registration schema)
# Logic: validate → check duplicate → create user → return user response
# Responses: 201 Created, 409 Conflict, 422 Validation Error
```

### 4. Implement login endpoint

```
# POST /auth/login
# Input: email, password (via login schema)
# Logic: authenticate → generate token → return token response
# Responses: 200 OK, 401 Unauthorized
```

### 5. Implement current user endpoint

```
# GET /auth/me
# Auth: requires valid JWT token (via middleware)
# Logic: extract user from token → return user response
# Responses: 200 OK, 401 Unauthorized
```

### 6. Implement token refresh endpoint

```
# POST /auth/refresh
# Auth: requires valid JWT token
# Logic: validate current token → generate new token → return token response
# Responses: 200 OK, 401 Unauthorized
```

### 7. Mount routes on app

- Register auth router on the application
- Configure CORS if needed

### 8. Run all tests

```bash
# All integration tests should pass
# Also run full test suite to ensure no regressions
```

### 9. Commit

```bash
git add .
git commit -m "feat(auth): implement API endpoints

- Add POST /auth/register with validation and duplicate check
- Add POST /auth/login with credential verification
- Add GET /auth/me with token-based authentication
- Add POST /auth/refresh for token renewal
- Add integration tests for all endpoints
"
```

## Acceptance Criteria

- [ ] All four endpoints implemented and reachable
- [ ] Registration validates input and rejects duplicates
- [ ] Login returns JWT token on success
- [ ] Protected endpoints reject requests without valid token
- [ ] Token refresh issues a new valid token
- [ ] All integration tests pass
- [ ] Full test suite passes (no regressions)

## Dependencies

- **Depends on**: auth-logic
- **Required by**: none (final task)

## Estimated Time

2-3 hours
