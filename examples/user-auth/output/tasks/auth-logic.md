# Task: Authentication Logic Implementation

## Goal

Implement password hashing, JWT token generation/validation, CRUD operations, and authentication middleware.

## Files Involved

- Create: src/auth/security (password hashing, JWT creation/validation)
- Create: src/auth/crud (user CRUD operations)
- Create: src/auth/middleware (get_current_user dependency)
- Create: tests/auth/test_security (security function tests)
- Create: tests/auth/test_crud (CRUD operation tests)

## Steps

### 1. Write tests for security functions

```
# tests/auth/test_security
# Verify that:
# - Password hashing produces different hash each time
# - Password verification succeeds with correct password
# - Password verification fails with incorrect password
# - JWT token contains correct user ID and expiration
# - Expired token raises appropriate error
# - Invalid token raises appropriate error
```

### 2. Run tests (should fail)

```bash
# Expected: security module not found
```

### 3. Implement password hashing

- Use bcrypt (or equivalent) with cost factor >= 12
- `hash_password(plain: str) -> str`
- `verify_password(plain: str, hashed: str) -> bool`

### 4. Implement JWT functions

- `create_access_token(user_id: str, expires_delta: timedelta) -> str`
- `decode_access_token(token: str) -> dict`
- Use HS256 algorithm, secret from environment

### 5. Run security tests (should pass)

### 6. Write tests for CRUD operations

```
# tests/auth/test_crud
# Verify that:
# - Create user stores hashed password (not plain text)
# - Get user by email returns correct user
# - Get user by email returns None for non-existent user
# - Duplicate email raises appropriate error
```

### 7. Implement CRUD operations

- `create_user(db, email, password) -> User`
- `get_user_by_email(db, email) -> User | None`
- `authenticate_user(db, email, password) -> User | None`

### 8. Run CRUD tests (should pass)

### 9. Implement authentication middleware

- Extract token from Authorization header
- Decode and validate token
- Load user from database
- Return user object or raise 401

### 10. Run all tests

```bash
# All security, CRUD, and middleware tests should pass
```

### 11. Commit

```bash
git add .
git commit -m "feat(auth): implement authentication logic

- Add password hashing with bcrypt
- Add JWT token creation and validation
- Add user CRUD operations
- Add authentication middleware
- Add comprehensive tests for all auth logic
"
```

## Acceptance Criteria

- [ ] Passwords are hashed before storage (never stored in plain text)
- [ ] JWT tokens include user ID and expiration
- [ ] Expired/invalid tokens are properly rejected
- [ ] CRUD operations handle duplicate emails
- [ ] Authentication middleware extracts and validates tokens
- [ ] All tests pass

## Dependencies

- **Depends on**: models
- **Required by**: api

## Estimated Time

3-4 hours
