# User Authentication System

## Requirements Overview

Implement a JWT-based user authentication system that supports registration, login, and token refresh.

## Functional Requirements

### 1. User Registration
- Users register with email and password
- Email must be unique
- Passwords must be stored hashed
- Return user info (without password)

### 2. User Login
- Users log in with email and password
- Return a JWT token on success
- Token contains user ID and expiration
- Token validity is 24 hours

### 3. Token Refresh
- Exchange a valid token for a new token
- Extend the login session

### 4. Get User Info
- Use token to fetch current user info
- Token validity must be verified

## Technical Requirements

### Backend
- Web framework with routing and middleware support
- Language runtime and package manager

### Database
- Relational database for user storage
- ORM or query builder for database operations

### Security
- Hash passwords with bcrypt or equivalent
- Use JWT for authentication
- Sign tokens with HS256

### Testing
- Unit testing framework
- Code coverage tool
- Target coverage >= 80%

## Data Model

### User Table
```
- id: UUID (primary key)
- email: String (unique, not null)
- hashed_password: String (not null)
- created_at: DateTime
- updated_at: DateTime
```

## API Endpoints

### POST /auth/register
Register a new user

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2025-02-13T10:00:00Z"
}
```

### POST /auth/login
User login

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### POST /auth/refresh
Refresh token

**Headers:**
```
Authorization: Bearer {current_token}
```

**Response:**
```json
{
  "access_token": "new_jwt_token_string",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### GET /auth/me
Get current user info

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2025-02-13T10:00:00Z"
}
```

## Error Handling

- 400 Bad Request - invalid request parameters
- 401 Unauthorized - unauthorized or invalid token
- 409 Conflict - email already exists
- 500 Internal Server Error - server error

## Non-Functional Requirements

### Performance
- Login response time < 500ms
- Registration response time < 1s

### Security
- Minimum password length is 8
- Tokens are signed with a strong random secret key
- bcrypt cost factor >= 12 (or equivalent)

### Maintainability
- Code coverage >= 80%
- Follow language-appropriate style guide
- Key logic is documented
