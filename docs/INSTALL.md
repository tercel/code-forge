# Code Forge Installation Guide

## Installation to Claude Code

### Method 1: Install from Local (Development Mode)

```bash
# 1. Enter skills directory
cd /Users/tercel/WorkSpace/skills

# 2. Confirm code-forge directory exists
ls -la code-forge/

# 3. Claude Code will auto-detect skills in this directory
# Start Claude Code with skills directory specified
claude --skills-dir /Users/tercel/WorkSpace/skills
```

### Method 2: Symbolic Link (Recommended)

```bash
# 1. Find Claude Code skills directory
# Usually at ~/.claude/skills/ or similar

# 2. Create symbolic link
ln -s /Users/tercel/WorkSpace/skills/code-forge ~/.claude/skills/code-forge

# 3. Restart Claude Code
```

### Method 3: Copy Install

```bash
# Copy entire code-forge directory to Claude Code skills directory
cp -r /Users/tercel/WorkSpace/skills/code-forge ~/.claude/skills/
```

## Verify Installation

After starting Claude Code, check if the skill is available:

```
/help skills
```

You should see `forge` skill listed in available skills.

## Preparation Before Use

### 1. Create Documentation Directory in Project

```bash
cd your-project/
mkdir -p planning/features
```

### 2. Create First Feature Document

```bash
cat > planning/features/my-feature.md <<'EOF'
# My Feature

## Requirements
Describe the feature you want to implement...

## Technical Requirements
- Technology stack to use...
EOF
```

### 3. Run Forge

```
/forge @planning/features/my-feature.md
```

## Configuration (Optional)

### Customize Output Directory

Default output to `planning/implementation/`. To customize, create `.code-forge.json` in your project root.
See [CONFIGURATION.md](./CONFIGURATION.md) for details.

### Git Configuration

Recommended to add to `.gitignore`:

```gitignore
# If you don't want to commit status files
planning/implementation/**/state.json

# Or keep status files, ignore temp files
# planning/implementation/**/.code-forge-temp/
```

Recommended to commit `state.json` for team collaboration.

## Update

```bash
cd /Users/tercel/WorkSpace/skills/code-forge
git pull  # If installed from Git repository

# Or manually update files
```

## Uninstall

```bash
# If it's a symbolic link
rm ~/.claude/skills/code-forge

# If it's a copy install
rm -rf ~/.claude/skills/code-forge
```

## Troubleshooting

### Issue 1: Skill Not Displayed

**Check:**
```bash
# Confirm skills directory structure
ls -la ~/.claude/skills/code-forge/skills/forge/
# Should see SKILL.md
```

**Solution:**
- Ensure SKILL.md exists and is properly formatted
- Restart Claude Code

### Issue 2: Cannot Create Files

**Check:**
```bash
# Confirm write permission in current directory
touch test.txt && rm test.txt
```

**Solution:**
- Switch to directory with write permission
- Check if `planning/` directory exists

### Issue 3: Generated Files Location Is Wrong

**Check:**
- Ensure running `/forge` from project root
- Check `.code-forge.json` for custom directory settings

**Solution:**
- Create `planning/features/` in project root
- Or customize directories via `.code-forge.json`

## Need Help?

- See examples: `examples/user-auth/`
- Read documentation: `README.md`
- Check file structure standards: `FILE_STRUCTURE.md`
