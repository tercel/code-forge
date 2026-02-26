# Using Code Forge in Existing Projects

> How to use Code Forge in projects that are in progress or already completed

**Applicable scenarios**:
- ✅ Project has been in development for a while
- ✅ Some features completed, others still in development
- ✅ Project completed, wanting to add planning documentation
- ✅ Want to standardize existing development workflows

---

## Quick Answers

### Q1: Can I use Code Forge on an already started project?

**✅ Yes!** Code Forge supports three usage modes:

1. **Retrospective mode** - Generate planning documentation for completed code
2. **Hybrid mode** - Part completed + future planning
3. **Forward-looking mode** - Only plan future functionality

### Q2: Can I use it on a completed project?

**✅ Yes!** Main purposes:

- Generate documentation for team reference
- Provide planning templates for similar projects
- Review and knowledge consolidation
- Provide task decomposition reference for future maintenance

---

## Usage Methods

### Method 1: Retrospective Mode (Code written, add planning)

**Scenario**: Your `user-auth` feature is already complete, want to add planning documentation.

#### Step 1: Create feature document (describe what's done)

```bash
cd your-project/
mkdir -p docs/features

# Create document describing completed functionality
cat > docs/features/user-auth.md << 'EOF'
# User Authentication System (Completed)

## Feature Description
Implemented JWT-based user authentication system

## Implemented Features
- ✅ User registration (POST /auth/register)
- ✅ User login (POST /auth/login)
- ✅ Token verification middleware
- ✅ Password encryption (bcrypt)
- ✅ Token refresh mechanism

## Technical Implementation
- FastAPI
- JWT (python-jose)
- PostgreSQL
- SQLAlchemy ORM

## File List
- `src/auth/models.py` - User model
- `src/auth/routes.py` - Authentication routes
- `src/auth/schemas.py` - Pydantic schemas
- `src/auth/utils.py` - JWT utilities
- `tests/test_auth.py` - Test file
EOF
```

#### Step 2: Run Forge to generate plan

```bash
/code-forge:plan @docs/features/user-auth.md
```

**Forge will prompt**:
```
Detected keywords like "completed", "implemented" in document

Is this a completed feature?
  1. Yes - Generate retrospective planning (reflect completed work)
  2. No - Generate forward-looking plan (to be implemented)
  3. Hybrid - Part completed, part to do
```

Select **1 - Yes**, Forge will:
- Generate planning document with task status marked as `completed`
- Create task breakdown mapping to existing code files
- Generate state.json with 100% progress

#### Step 3: Manually align tasks and code

The generated plan will be at:
```
planning/user-auth/
├── overview.md
├── plan.md
├── tasks/
│   ├── user-model.md           # Maps to src/auth/models.py
│   ├── jwt-utils.md            # Maps to src/auth/utils.py
│   ├── auth-routes.md          # Maps to src/auth/routes.py
│   ├── schemas.md              # Maps to src/auth/schemas.py
│   └── tests.md                # Maps to tests/test_auth.py
└── state.json                  # All tasks marked as completed
```

**Manual adjustment**:
```json
{
  "feature": "user-auth",
  "status": "completed",
  "created_at": "2025-02-10T10:00:00Z",
  "completed_at": "2025-02-10T10:00:00Z",  // Actual completion time
  "progress": {
    "completed": 5,
    "total_tasks": 5,
    "percentage": 100
  },
  "tasks": [
    {
      "id": "task-001",
      "title": "Implement user model",
      "status": "completed",
      "files": ["src/auth/models.py"],  // Add actual file paths
      "completed_at": "2025-01-15"      // Actual completion time
    },
    ...
  ]
}
```

#### Value

- 📚 **Documentation**: Existing code now has planning documentation
- 🔍 **Traceable**: New team members can understand how feature is decomposed
- 📋 **Template**: Similar features can reuse this plan

---

### Method 2: Hybrid Mode (Part completed + part pending)

**Scenario**: `user-auth` basic functionality complete, but OAuth and 2FA not done.

#### Step 1: Create hybrid status document

```markdown
# User Authentication System

## Feature Description
Complete user authentication and authorization system

## Completed Features ✅
- User registration and login (password-based)
- JWT Token generation and verification
- Basic permission control

## To Be Implemented ⏸️
- OAuth third-party login (Google, GitHub)
- Two-factor authentication (2FA)
- Fine-grained permission system (RBAC)
- Session management

## Technology Stack
- Current: web framework, JWT, relational database
- Planned: OAuth2, TOTP (2FA), session store
```

#### Step 2: Run Forge

```bash
/code-forge:plan @docs/features/user-auth.md
```

Select **3 - Hybrid**, Forge will ask:

```
Mark which features are completed:
  [x] User registration and login
  [x] JWT Token generation and verification
  [x] Basic permission control
  [ ] OAuth third-party login
  [ ] Two-factor authentication
  [ ] RBAC permission system
  [ ] Session management
```

#### Step 3: Generated plan

```
planning/user-auth/
├── overview.md
├── plan.md
├── tasks/
│   ├── ✅ basic-auth.md         (completed)
│   ├── ✅ jwt.md                (completed)
│   ├── ✅ basic-permissions.md  (completed)
│   ├── ⏸️ oauth.md              (pending)
│   ├── ⏸️ 2fa.md                (pending)
│   ├── ⏸️ rbac.md               (pending)
│   └── ⏸️ session.md            (pending)
└── state.json
```

**state.json**:
```json
{
  "status": "in_progress",
  "progress": {
    "completed": 3,
    "total_tasks": 7,
    "percentage": 43
  },
  "tasks": [
    {"id": "task-001", "status": "completed", "title": "Basic authentication"},
    {"id": "task-002", "status": "completed", "title": "JWT implementation"},
    {"id": "task-003", "status": "completed", "title": "Basic permissions"},
    {"id": "task-004", "status": "pending", "title": "OAuth integration"},
    {"id": "task-005", "status": "pending", "title": "2FA implementation"},
    {"id": "task-006", "status": "pending", "title": "RBAC system"},
    {"id": "task-007", "status": "pending", "title": "Session management"}
  ]
}
```

#### Step 4: Continue development

Now you can continue with pending tasks:

```bash
# View next task
cat planning/user-auth/tasks/04-oauth.md

# Or let Forge execute
/code-forge:impl user-auth
# Will start from task-004
```

---

### Method 3: Forward-looking Mode (Only plan future)

**Scenario**: Project has some features, now adding new `payment-gateway` feature.

#### Use standard flow directly

```bash
# 1. Create new feature document (only describe new features)
vim docs/features/payment-gateway.md

# 2. Run Forge
/code-forge:plan @docs/features/payment-gateway.md

# 3. Generated plan is completely new
planning/payment-gateway/
└── All tasks status are pending
```

**Unrelated to existing code**, this is standard Code Forge usage.

---

## Handling Multi-module Projects

### Scenario: APCore Python Project (6 modules, partially complete)

#### Current Status
```
✅ 01-foundation      - Completed
✅ 02-schema-system   - Completed
🔄 03-registry        - In progress (75%)
🔄 04-executor        - In progress (40%)
⏸️ 05-decorator       - Not started
⏸️ 06-observability   - Not started
```

#### Using Code Forge

**Step 1: Create overview.md**

```bash
cd apcore-python/
cp /path/to/code-forge/templates/overview.md planning/
vim planning/overview.md
```

Fill in module status, dependencies, implementation order (see `examples/apcore-python-overview.md`).

**Step 2: Create documents for each module**

Completed modules (retrospective):
```bash
# Describe completed foundation
cat > docs/features/01-foundation.md << 'EOF'
# 01-Foundation Module (Completed)

## Feature Description
Provides framework infrastructure and core abstractions

## Implemented Components ✅
- Pattern base class
- IDConverter utilities
- ModuleABC abstract base
- Context context
- Configuration system
- Error handling

## File List
- src/apcore/foundation/pattern.py
- src/apcore/foundation/id_converter.py
- src/apcore/foundation/module.py
- ...
EOF

/code-forge:plan @docs/features/01-foundation.md
# Select "Retrospective mode"
```

In-progress modules (hybrid):
```bash
# Describe registry completed and pending
cat > docs/features/03-registry.md << 'EOF'
# 03-Registry Service Registration and Discovery

## Completed ✅
- Registry basic implementation
- Service registration mechanism
- Basic query API

## To Be Implemented ⏸️
- Service discovery optimization
- Dependency injection container
- Health check integration
EOF

/code-forge:plan @docs/features/03-registry.md
# Select "Hybrid mode"
```

Not started modules (standard):
```bash
# Standard forward-looking plan
cat > docs/features/05-decorator.md << 'EOF'
# 05-Module Decorator

## Feature Description
Module decorator system, providing automatic binding and configuration injection

## Core Requirements
- Decorator design
- Automatic binding mechanism
- Configuration injection
- Metadata collection
EOF

/code-forge:plan @docs/features/05-decorator.md
# Select "Standard mode"
```

**Step 3: Final structure**

```
docs/
└── features/                              # Input documents
    ├── 01-foundation.md                  # Completed (retrospective)
    ├── 02-schema-system.md               # Completed (retrospective)
    ├── 03-registry.md                    # Hybrid
    ├── 04-executor.md                    # Hybrid
    ├── 05-decorator.md                   # Forward-looking
    └── 06-observability.md               # Forward-looking
planning/
├── overview.md                            # Project overview
├── 01-foundation/
│   ├── plan.md
│   ├── tasks/  (all completed)
│   └── state.json (100%)
├── 02-schema-system/
│   └── state.json (100%)
├── 03-registry/
│   └── state.json (75%)
├── 04-executor/
│   └── state.json (40%)
├── 05-decorator/
│   └── state.json (0%)
└── 06-observability/
    └── state.json (0%)
```

#### Maintain overview.md

Update overview manually or automatically:

```bash
# Manually update progress
vim planning/overview.md

# Or use script to sync (P1 feature)
# Or use a script to sync progress
```

---

## Practical Examples

### Example 1: Add documentation to completed features

**Background**: Your project has user authentication functionality, code in `src/auth/`.

```bash
# 1. Create project configuration (if not yet)
cat > .code-forge.json << 'EOF'
{
  "directories": {
    "base": "planning/"
  }
}
EOF

# 2. Create features directory
mkdir -p docs/features

# 3. Write feature document (describe what's done)
cat > docs/features/user-auth.md << 'EOF'
# User Authentication (Completed)

## Implemented Features
- User registration: POST /auth/register
- User login: POST /auth/login
- JWT Token verification
- Password encryption

## Technical Implementation
- FastAPI
- python-jose (JWT)
- bcrypt (password encryption)
- PostgreSQL

## Existing Files
- src/auth/models.py
- src/auth/routes.py
- src/auth/schemas.py
- src/auth/utils.py
- tests/test_auth.py
EOF

# 4. Run Forge (retrospective mode)
/code-forge:plan @docs/features/user-auth.md
# Select: 1 - Retrospective mode

# 5. Generated plan is at
ls planning/user-auth/
# overview.md  plan.md  tasks/  state.json

# 6. View generated plan
cat planning/user-auth/plan.md

# 7. Manually align file paths (edit state.json)
vim planning/user-auth/state.json
# Add actual file paths to each task
```

---

### Example 2: Hybrid mode (Part completed + expansion)

**Background**: Authentication basics complete, adding OAuth and 2FA.

```bash
# 1. Write hybrid document
cat > docs/features/auth-enhancement.md << 'EOF'
# Authentication Feature Enhancement

## Completed Basic Features ✅
- Username/password login
- JWT Token
- Basic permissions

## Planned New Features ⏸️
- OAuth2 third-party login
  - Google OAuth
  - GitHub OAuth
- Two-factor authentication (2FA)
  - TOTP support
  - SMS verification
- Advanced permission control
  - RBAC system
  - Resource-level permissions
EOF

# 2. Run Forge
/code-forge:plan @docs/features/auth-enhancement.md

# Forge asks:
# "Detected hybrid state, which features are completed?"
# Check completed parts

# 3. Generated tasks have mixed status
ls planning/auth-enhancement/tasks/
# ✅ basic-auth.md          (completed)
# ✅ jwt.md                 (completed)
# ⏸️ google-oauth.md        (pending)
# ⏸️ github-oauth.md        (pending)
# ⏸️ totp-2fa.md            (pending)
# ⏸️ rbac.md                (pending)

# 4. Continue development of pending parts
/code-forge:impl auth-enhancement
# Will start from first pending task
```

---

## FAQ

### Q1: What's the value of generating a plan for a completed project?

**Value**:
1. **Documentation**: New team members quickly understand project structure
2. **Knowledge consolidation**: Record "how we did it back then"
3. **Template reuse**: Next similar project can reference it
4. **Maintenance reference**: Future changes know each part's responsibility
5. **Training material**: Show new people task decomposition thinking

### Q2: In retrospective mode, what if tasks don't match code exactly?

**Normal situation**: Actual development often differs from ideal planning.

**Handling**:
1. **Use generated plan as reference**: Don't force 100% match
2. **Manual adjustment**: Edit task file to reflect actual situation
3. **Add comments**: Note in task "differences between actual and planned"

**Example**:
```markdown
<!-- tasks/03-jwt-implementation.md -->

# Task 3: JWT Token Implementation

## Planned Implementation
- Use python-jose library
- HS256 algorithm

## Actual Implementation ✅
- Used PyJWT library (team already has dependency)
- Changed to RS256 algorithm (more secure)
- Added Token refresh mechanism (not in original plan)

## Files
- src/auth/jwt_utils.py (actual)
- src/auth/token_refresh.py (added)
```

### Q3: Multi-module project with inter-module dependencies, how to handle?

**Use overview.md**:

1. Create project-level `planning/overview.md`
2. Define module dependencies (Mermaid diagram)
3. Run Forge separately for each module
4. Maintain overall progress in overview.md

**See**: `examples/apcore-python-overview.md`

### Q4: Large project with dozens of features, generate plans for all?

**Recommendation**:

**Not necessary to generate all**, use selectively:

1. **Core features** - Generate plans (help new people understand)
2. **Complex features** - Generate plans (record tech decisions)
3. **Simple features** - Can skip (cost > benefit)

**Example judgment**:
```
✅ Generate: User authentication, payment gateway, permission system (core complex)
❌ Skip: Configuration file reading, logging utilities (simple helpers)
```

### Q5: Existing project code is messy, can Forge help refactor?

**Code Forge positioning**: Planning tool, not refactoring tool.

**But can use it this way**:

1. **Create "ideal plan"**: Describe how feature should be implemented
2. **Compare with current**: See how far existing code deviates
3. **Identify refactor points**: Which parts need refactoring
4. **Step-by-step refactor**: Break refactoring into small tasks

**Example**:
```markdown
# User Authentication Refactor Plan

## Current Problems
- All logic in one 1000-line file
- No tests
- High coupling

## Ideal Structure (Forge generated)
- models.py (data models)
- services.py (business logic)
- routes.py (API endpoints)
- utils.py (utilities)
- tests/ (testing)

## Refactor Tasks
- [ ] Task 1: Extract data models
- [ ] Task 2: Separate business logic
- [ ] Task 3: Write tests
- [ ] Task 4: Split routes
```

---

## Best Practices

### ✅ Recommended

1. **Clarify current status first**
   - List existing features and code files
   - Identify what's completed vs pending

2. **Process by module**
   - Large projects run Forge separately for each module
   - Use overview.md to coordinate overall

3. **Pragmatic approach**
   - Plans are reference, not doctrine
   - Actual code deviating from plan is normal

4. **Incremental use**
   - First generate plans for core modules
   - Gradually cover other modules

5. **Continuous maintenance**
   - Regularly update state.json progress
   - Keep overview.md in sync

### ❌ Not Recommended

1. **Force alignment**: Spend excessive time making plan perfectly match code
2. **Duplicate work**: Already have good docs, don't need to generate again
3. **Over-planning**: Generate detailed plans for simple features
4. **Ignore current status**: Generated plan completely disregards existing code

---

## Summary

| Scenario | Usage Mode | Value |
|----------|------------|-------|
| **Completed project** | Retrospective mode | Documentation, knowledge consolidation, template reuse |
| **In-progress project** | Hybrid mode | Current status record + future planning |
| **New feature addition** | Forward-looking mode | Standard Forge workflow |
| **Multi-module project** | overview.md + per-module | Global view + detailed planning |

**Core principle**: Code Forge is a flexible tool that adapts to any project stage. No need to stick to "must start from scratch" thinking.

---

**Related documents**:
- [OVERVIEW_GUIDE.md](./OVERVIEW_GUIDE.md) - Multi-module project management
- [README.md](../README.md) - Full command reference and quick start

**Last updated**: 2026-02-26
