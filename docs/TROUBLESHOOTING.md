# Code Forge Troubleshooting Guide

> Common issues and solutions

## Quick Diagnosis

When encountering problems, first check:

```bash
# 1. Check configuration
cat .code-forge.json

# 2. Check file structure
ls -la planning/

# 3. Check permissions
ls -ld planning/
```

---

## Configuration-Related Issues

### Q1: Configuration file not taking effect

**Symptom:**
```
Created .code-forge.json but Forge is still using default configuration
```

**Causes:**
1. Configuration file not in project root directory
2. JSON format error
3. Filename spelling error

**Solution:**

```bash
# 1. Confirm file location
pwd  # View current directory
ls -la .code-forge.json  # Confirm file exists

# 2. Validate JSON format
cat .code-forge.json | jq .

# 3. Check filename
ls -la | grep code-forge
# Should be .code-forge.json
# Not .forge.json
# Not code-forge.json
```

**Correct configuration:**
```json
{
  "directories": {
    "base": "planning/"
  }
}
```

---

### Q2: Configuration validation failed

**Symptom:**
```
❌ Configuration validation failed
Error: directories.base cannot contain '..'
```

**Cause:**
Configuration value doesn't meet security or format requirements

**Solution:**

```bash
# Check configuration content
cat .code-forge.json

# Common issues:
# ❌ "base": "../planning/"  # cannot contain ..
# ❌ "base": "src/"          # not recommended for source code directory
# ❌ "commit_state_file": "true"  # should be boolean not string

# ✅ Correct example:
{
  "directories": {
    "base": "planning/"  # ✓ relative path, no ..
  },
  "git": {
    "commit_state_file": true  # ✓ boolean type
  }
}
```

---

### Q3: Configuration priority unclear

**Symptom:**
```
Don't know which configuration is in effect
```

**Solution:**

Check Forge startup output:
```
📋 Code Forge Configuration
├── Base directory: dev-plans/
├── Configuration sources:
│   ├── System default: ✓
│   ├── User configuration: ~/.code-forge.json ✓
│   └── Project configuration: .code-forge.json ✓
└── Final priority: Project configuration
```

**Priority Order:**
```
Command-line arguments > Project configuration > User configuration > System default
```

**Debug Tips:**
```bash
# View global user configuration
cat ~/.code-forge.json

# View project configuration
cat .code-forge.json

# Temporarily ignore all configurations
/code-forge:plan @xxx.md --ignore-config
```

---

## File and Directory Issues

### Q4: Input document not found

**Symptom:**
```
❌ Input document not found
File: docs/features/user-auth.md
```

**Cause:**
1. File path error
2. File doesn't exist
3. Spelling error

**Solution:**

```bash
# 1. List available files
ls docs/features/

# 2. Check spelling
# user-auth.md ✓
# user-atuh.md ❌ (spelling error)
# userauth.md  ❌ (missing hyphen)

# 3. Confirm full path
ls -la docs/features/user-auth.md

# 4. Check current directory
pwd  # Ensure in project root directory
```

**Correction Example:**
```bash
# ❌ Wrong
/code-forge:plan @features/user-auth.md  # Missing planning/

# ✅ Correct
/code-forge:plan @docs/features/user-auth.md
```

---

### Q5: Generated files in wrong location

**Symptom:**
```
Files generated in wrong directory
Expected: planning/
Actual: some/other/path/
```

**Cause:**
Directory setting in configuration doesn't match expectation

**Solution:**

```bash
# 1. Check configuration
cat .code-forge.json

# 2. Confirm base directory
{
  "directories": {
    "base": "docs/"  # ← This determines the base directory
  }
}

# 3. Modify configuration
vim .code-forge.json

# Change to:
{
  "directories": {
    "base": "planning/"
  }
}

# 4. Run again
/code-forge:plan @docs/features/xxx.md
```

---

### Q6: Directory already exists conflict

**Symptom:**
```
⚠️ Target directory already exists
Directory: planning/user-auth/
```

**Cause:**
Previously generated or manually created directory with same name

**Solution:**

```bash
# Option A: Resume mode (recommended)
# If state.json exists, Forge will auto-resume
ls planning/user-auth/state.json

# Option B: Backup then regenerate
mv planning/user-auth \
   planning/user-auth.backup
/code-forge:plan @docs/features/user-auth.md

# Option C: Force overwrite (dangerous)
rm -rf planning/user-auth
/code-forge:plan @docs/features/user-auth.md
```

---

## Execution Issues

### Q7: Cannot resume execution

**Symptom:**
```
Previously paused task, now unable to continue
```

**Cause:**
1. state.json deleted
2. state.json format corrupted
3. Files moved location

**Solution:**

```bash
# 1. Check state.json
cat planning/user-auth/state.json

# 2. Validate format
cat planning/user-auth/state.json | jq .

# 3. If format error, fix manually
vim planning/user-auth/state.json

# 4. If deleted, regenerate
/code-forge:plan @docs/features/user-auth.md
# Select "Restart"
```

---

### Q8: Task execution stuck

**Symptom:**
```
Execution stops at certain task, unable to continue
```

**Cause:**
1. Task dependencies not met
2. state.json status anomaly
3. Script error

**Solution:**

```bash
# 1. Check task status
cat planning/user-auth/state.json | \
  jq . | grep -A 5 "status"

# 2. View current task
# Find task with status: "in_progress"

# 3. Update status manually (if needed)
vim planning/user-auth/state.json
# Change stuck task status to "pending"

# 4. Run again
/code-forge:plan @docs/features/user-auth.md
```

---

## Git-Related Issues

### Q9: Git conflict

**Symptom:**
```
git pull
CONFLICT: planning/user-auth/state.json
```

**Cause:**
Multiple people modified state.json simultaneously

**Solution:**

```bash
# Option A: Use local version
git checkout --ours planning/user-auth/state.json
git add planning/user-auth/state.json
git commit -m "resolve: keep local state.json"

# Option B: Use remote version
git checkout --theirs planning/user-auth/state.json
git add planning/user-auth/state.json
git commit -m "resolve: accept remote state.json"

# Option C: Manual merge
vim planning/user-auth/state.json
# Manually merge content
git add planning/user-auth/state.json
git commit -m "resolve: merge state.json manually"
```

**Prevention:**
```bash
# Pull before making changes
git pull
/code-forge:plan @docs/features/xxx.md
git add .
git commit -m "..."
git push
```

---

### Q10: Accidentally committed state.json

**Symptom:**
```
state.json changes frequently, polluting Git history
```

**Solution:**

```bash
# 1. Add to .gitignore
echo "**/state.json" >> .gitignore

# 2. Remove from Git (keep local file)
git rm --cached planning/**/state.json

# 3. Commit
git add .gitignore
git commit -m "chore: ignore state.json files"

# 4. Push
git push
```

---

## Performance Issues

### Q11: Generation process very slow

**Symptom:**
```
Generating plans and tasks takes a long time
```

**Cause:**
1. Document too large
2. Task decomposition too fine
3. Network issues (if using external services)

**Solution:**

```bash
# 1. Simplify input document
# Keep only core requirements, delete redundant content

# 2. Adjust task granularity
vim .code-forge.json
{
  "execution": {
    "task_granularity": "coarse"  # fine → medium → coarse
  }
}

# 3. Check network
# Code Forge itself doesn't need network
# But external tools may be slow if used
```

---

## Common Error Messages

### Error Code Table

| Error Message | Cause | Solution |
|---------|------|---------|
| `Configuration file format error` | JSON syntax error | Validate with jsonlint |
| `Directory not found` | Path configuration error | Check directories.base |
| `File is empty` | Input document has no content | Add requirement description |
| `Permission denied` | File permission issue | chmod +w or check owner |
| `state.json corrupted` | JSON format error | Fix manually or regenerate |
| `Circular dependency` | Module dependency loop | Redesign dependencies |

---

## Diagnostic Tools

### Configuration Check Script

```bash
#!/bin/bash
# check-config.sh - Check Code Forge configuration

echo "=== Code Forge Configuration Check ==="

# 1. Project root directory
echo "1. Project root directory"
if [ -d .git ]; then
    echo "  ✓ Git repository"
else
    echo "  ⚠️  Not a Git repository"
fi

# 2. Configuration files
echo "2. Configuration files"
if [ -f .code-forge.json ]; then
    echo "  ✓ Project configuration exists"
    if jq . .code-forge.json > /dev/null 2>&1; then
        echo "  ✓ JSON format correct"
    else
        echo "  ❌ JSON format error"
    fi
else
    echo "  - No project configuration (will use default)"
fi

if [ -f ~/.code-forge.json ]; then
    echo "  ✓ User configuration exists"
else
    echo "  - No user configuration"
fi

# 3. Directory structure
echo "3. Directory structure"
if [ -d planning ]; then
    echo "  ✓ planning/ exists"
    if [ -d docs/features ]; then
        echo "  ✓ docs/features/ exists"
        echo "    File count: $(ls docs/features/*.md 2>/dev/null | wc -l)"
    fi
    echo "  ✓ planning/ exists"
    echo "    Module count: $(ls -d planning/*/ 2>/dev/null | wc -l)"
else
    echo "  - planning/ doesn't exist (will auto-create)"
fi

# 4. Permissions
echo "4. Permission check"
if [ -w . ]; then
    echo "  ✓ Current directory writable"
else
    echo "  ❌ Current directory not writable"
fi
```

### Status Check Script

```bash
#!/bin/bash
# check-status.sh - Check all module status

echo "=== Code Forge Module Status ==="

for dir in planning/*/; do
    if [ -f "$dir/state.json" ]; then
        feature=$(basename "$dir")
        status=$(jq -r '.status' "$dir/state.json")
        completed=$(jq -r '.progress.completed' "$dir/state.json")
        total=$(jq -r '.progress.total_tasks' "$dir/state.json")

        echo "📦 $feature"
        echo "   Status: $status"
        echo "   Progress: $completed/$total"
        echo ""
    fi
done
```

---

## Getting Help

### Self-Help Resources

1. **View documentation**
   ```bash
   cat README.md
   cat QUICK_START.md
   cat CONFIGURATION.md
   ```

2. **Check examples**
   ```bash
   ls examples/
   cat examples/user-auth/output/plan.md
   ```

3. **Check configuration**
   ```bash
   cat templates/.code-forge.json
   ```

### Report Issues

If the problem cannot be resolved, provide when creating an issue:

```markdown
## Issue Description
[Describe the problem you encountered]

## Reproduction Steps
1. Create document xxx.md
2. Run /code-forge:plan @xxx.md
3. Error appears: ...

## Environment Information
- OS: macOS / Linux / Windows
- Claude Code Version:
- Code Forge Version:

## Configuration File
```json
[Paste .code-forge.json content]
```

## Error Message
```
[Paste complete error message]
```
```

---

## Common Misconceptions

### ❌ Wrong Approach

1. **Run Forge in src/ directory**
   ```bash
   cd src/
   /code-forge:plan @features/xxx.md  # ❌ Not in project root
   ```

2. **Use absolute paths**
   ```bash
   /code-forge:plan @/Users/xxx/project/features/xxx.md  # ❌ Use absolute path
   ```

3. **Confuse input and output directories**
   ```bash
   # Input: docs/features/xxx.md
   # Output: planning/xxx/
   # Don't confuse them
   ```

4. **Modify state.json without validation**
   ```bash
   vim state.json  # After modifying
   # ❌ Run directly, may have format error
   # ✅ First validate: cat state.json | jq .
   ```

### ✅ Correct Approach

1. **Run in project root directory**
   ```bash
   cd /path/to/project
   /code-forge:plan @docs/features/xxx.md
   ```

2. **Use relative paths**
   ```bash
   /code-forge:plan @docs/features/xxx.md  # ✅
   ```

3. **Understand directory structure**
   ```
   docs/features/     ← Input (documents you create)
   planning/ ← Output (generated by Forge)
   ```

4. **Validate after modifying**
   ```bash
   vim state.json
   jq . state.json  # Validate format
   /code-forge:plan @xxx.md  # Run again
   ```

---

**Last Updated**: 2026-02-26
