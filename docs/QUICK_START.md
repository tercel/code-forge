# Code Forge Quick Start

Get started with Code Forge in 5 minutes!

## 1. Create Feature Document (1 minute)

```bash
# At project root
mkdir -p planning/features

cat > planning/features/todo-list.md <<'EOF'
# Todo List Feature

## Requirements
Implement a simple todo list

## Features
- Add todo item
- Mark complete
- Delete item
- Display list

## Technology
- Web framework (your choice)
- Database (your choice)
- Testing framework
EOF
```

## 2. Run Forge (2 minutes)

In Claude Code:

```
/forge @planning/features/todo-list.md
```

Forge will:
1. ✅ Analyze your document
2. ✅ Ask supplementary questions (tech stack, test strategy, etc.)
3. ✅ Generate detailed implementation plan
4. ✅ Break down into executable tasks

## 3. View Generated Files (1 minute)

```bash
tree planning/implementation/todo-list/

# Output:
# planning/implementation/todo-list/
# ├── overview.md            # Feature overview + task execution order
# ├── plan.md                # Overall plan
# ├── tasks/                 # Task breakdown
# │   ├── setup.md
# │   ├── models.md
# │   ├── crud.md
# │   └── api.md
# └── state.json             # Status tracking
```

## 4. Execute Tasks (1 minute to start)

Choose execution method:

**Option A: Execute Immediately**
```
Forge will ask: "How to execute this plan?"
Select: "Start execution now"
```

Forge will guide you through each task one by one.

**Option B: Execute Manually**
```bash
# Read first task
cat planning/implementation/todo-list/tasks/setup.md

# Execute by steps
# 1. Write tests
# 2. Run tests (confirm failure)
# 3. Implement code
# 4. Run tests (confirm pass)
# 5. Commit code

# After completion, manually update state.json
# Or re-run /forge to continue next task
```

## 5. Track Progress

```bash
# Check current status
cat planning/implementation/todo-list/state.json

# Example output:
# {
#   "status": "in_progress",
#   "progress": {
#     "completed": 2,
#     "in_progress": 1,
#     "pending": 1
#   }
# }
```

## Complete Example

Want to see a complete example? Check:

```bash
cd /Users/tercel/WorkSpace/skills/code-forge/examples/user-auth/

# View input document
cat input/user-auth.md

# View generated plan
cat output/plan.md

# View task example
cat output/tasks/setup.md
```

## Compare with Traditional Method

### ❌ Traditional Way

```
1. Read requirement document
2. Think about implementation (30 min)
3. Start coding
4. Encounter issues, back to thinking (repeat)
5. Write tests at the end
6. Don't know progress status
```

### ✅ Code Forge Way

```
1. Write requirement document (or use existing)
2. /forge @document
3. Get detailed plan in 5 minutes
4. Execute by tasks (TDD way)
5. Track progress in real-time
6. Team can see status
```

## Key Advantages

1. **Save time** - Auto break down tasks, no manual planning
2. **TDD first** - Write tests first for each task
3. **Traceable** - Status tracking, always know progress
4. **Team friendly** - Standardized files, good for Git collaboration
5. **Recoverable** - Pause anytime, resume anytime

## Next Steps

- 📖 Read full documentation: `README.md`
- 🏗️ Learn file organization: `FILE_STRUCTURE.md`
- 💡 See more examples: `examples/`
- 🔧 Learn advanced usage: `SKILL.md`

## Common Usage

### New Feature Development
```
/forge @planning/features/new-feature.md
```

### Code Refactoring
```
/forge @planning/features/refactor-plan.md
```

### Bug Fix (if multiple steps required)
```
/forge @planning/features/bug-fix-plan.md
```

### Team Collaboration
```
/forge @planning/features/team-feature.md
# → Generate plan
# → Commit to Git
# → Team members assign tasks (modify state.json)
# → Execute individually, update status
```

Try it now! 🚀
