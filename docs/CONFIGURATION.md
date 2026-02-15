# Code Forge Configuration Guide

## Configuration File

Create `.code-forge.json` in the project root to customize Code Forge behavior.

**Why use `.code-forge.json` instead of `.forge.json`?**
- ✅ Avoid conflict with other tools (Minecraft Forge, Laravel Forge, etc.)
- ✅ More explicit identification as Code Forge configuration
- ✅ Consistent with project name

## Default Directory Structure (Without Configuration)

```
project/
├── planning/                    # Default base directory
│   ├── features/                # Default input document location
│   │   └── user-auth.md
│   └── implementation/          # Default output location
│       └── user-auth/
│           ├── overview.md
│           ├── plan.md
│           ├── tasks/
│           └── state.json
```

## Complete Configuration Example

```json
{
  "version": "1.0",

  "_tool": {
    "name": "code-forge",
    "description": "Transform documentation into actionable development plans with task breakdown and status tracking",
    "url": "https://github.com/tercel/code-forge",
    "skills_collection": "https://github.com/tercel/claude-code-skills"
  },

  "directories": {
    "base": "planning/",           // Base directory
    "input": "features/",          // Input documentation subdirectory
    "output": "implementation/"    // Output planning subdirectory
  },

  "naming": {
    "feature_prefix": "",          // Feature directory prefix
    "task_prefix": "",             // Task file prefix
    "use_date": false              // Whether to use date prefix
  },

  "git": {
    "auto_commit": false,          // Auto-commit after file generation
    "commit_state_file": true,     // Whether to commit state.json
    "gitignore_patterns": [        // Auto-add to .gitignore
      "**/.code-forge-temp/"
    ]
  },

  "execution": {
    "default_mode": "ask",          // ask | manual | auto
    "auto_tdd": true,              // Auto-use TDD
    "task_granularity": "medium"   // fine | medium | coarse
  }
}
```

## Common Configuration Scenarios

### Scenario 1: Use Separate Planning Directory (Recommended)

Avoid conflict with existing `docs/`:

```json
{
  "directories": {
    "base": "planning/",
    "input": "features/",
    "output": "implementation/"
  }
}
```

**Result:**
```
project/
├── docs/              # Existing documentation (unchanged)
├── planning/
│   ├── features/      # Input
│   └── implementation/  # Output
```

### Scenario 2: Use docs Subdirectory

If your `docs/` directory has no conflict:

```json
{
  "directories": {
    "base": "docs/",
    "input": "specs/",
    "output": "implementation/"
  }
}
```

**Result:**
```
project/
└── docs/
    ├── specs/           # Input
    └── implementation/  # Output
```

### Scenario 3: Use Hidden Directory

Don't want to see planning files in project root:

```json
{
  "directories": {
    "base": ".dev/",
    "input": "specs/",
    "output": "plans/"
  },
  "git": {
    "commit_state_file": false,
    "gitignore_patterns": [".dev/"]
  }
}
```

**Result:**
```
project/
└── .dev/              # Hidden directory
    ├── specs/
    └── plans/

# .gitignore
.dev/                  # Don't commit
```

### Scenario 4: Separate Input and Output

Store input documentation and implementation planning separately:

```json
{
  "directories": {
    "base": "",                    // Empty = project root
    "input": "specs/features/",    // Absolute path
    "output": "dev/implementation/"  // Absolute path
  }
}
```

**Result:**
```
project/
├── specs/
│   └── features/      # Input documentation
└── dev/
    └── implementation/  # Implementation planning
```

### Scenario 5: Team Collaboration Mode

Configuration suitable for team sharing:

```json
{
  "directories": {
    "base": "project/",
    "input": "requirements/",
    "output": "tasks/"
  },
  "git": {
    "commit_state_file": true,     // Commit state file, team can see
    "gitignore_patterns": []       // Don't ignore any files
  },
  "execution": {
    "default_mode": "manual"       // Manual execution, better for collaboration
  }
}
```

**Result:**
```
project/
└── project/
    ├── requirements/    # Shared requirements documentation
    └── tasks/           # Shared task planning
        └── feature-x/
            └── state.json  # Commit to Git, team can see progress
```

## Configuration Field Details

### _tool (Read-Only)

The `_tool` section identifies the Code Forge plugin itself. It helps new team members understand what `.code-forge.json` is and where to install the tool.

| Field | Type | Value | Description |
|-------|------|-------|-------------|
| `name` | string | `"code-forge"` | Plugin name |
| `description` | string | `"Transform documentation..."` | What this tool does |
| `url` | string | `"https://github.com/tercel/code-forge"` | Plugin repository URL for installation |
| `skills_collection` | string | `"https://github.com/tercel/claude-code-skills"` | Parent skills collection URL |

**Why include this?**
- A new team member sees `.code-forge.json` in the project and immediately knows:
  - What tool this config belongs to
  - Where to install it (click the `url`)
  - What skills collection it's part of
- This is auto-populated when generating `.code-forge.json` from the template
- These values are read-only — user/project overrides do not change them

### directories

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `base` | string | `"planning/"` | Base directory, root path for all files |
| `input` | string | `"features/"` | Input documentation path relative to base |
| `output` | string | `"implementation/"` | Output planning path relative to base |

**Path Rules:**
- Relative path: relative to project root
- Absolute path: from project root
- Empty string: represents project root

**Examples:**
```json
// Relative paths
{"base": "planning/"}          // → project/planning/
{"base": "docs/dev/"}          // → project/docs/dev/

// Absolute path (from project root)
{"base": "planning/"}          // → project/planning/

// Empty path (project root)
{"base": ""}                   // → project/
```

### naming

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `feature_prefix` | string | `""` | Feature directory name prefix |
| `task_prefix` | string | `""` | Task file name prefix |
| `use_date` | boolean | `false` | Whether to use date prefix (like superpowers)|

**Examples:**
```json
// No prefix (default, recommended)
{
  "naming": {
    "feature_prefix": "",
    "task_prefix": ""
  }
}
// Result:
// → user-auth/
// → tasks/01-setup.md

// Use date prefix
{
  "naming": {
    "use_date": true
  }
}
// Result:
// → 2025-02-13-user-auth/
// → tasks/2025-02-13-01-setup.md

// Custom prefix
{
  "naming": {
    "feature_prefix": "feat-",
    "task_prefix": "task-"
  }
}
// Result:
// → feat-user-auth/
// → tasks/task-01-setup.md
```

### git

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `auto_commit` | boolean | `false` | Auto-commit after file generation |
| `commit_state_file` | boolean | `true` | Whether to commit state.json |
| `gitignore_patterns` | array | `[]` | Patterns to auto-add to .gitignore |

**Examples:**
```json
// Recommended: commit plans, don't commit status
{
  "git": {
    "auto_commit": false,
    "commit_state_file": false,
    "gitignore_patterns": ["**/state.json"]
  }
}

// Team collaboration: commit everything
{
  "git": {
    "auto_commit": false,
    "commit_state_file": true,
    "gitignore_patterns": []
  }
}

// Personal project: commit nothing
{
  "git": {
    "auto_commit": false,
    "commit_state_file": false,
    "gitignore_patterns": ["planning/"]
  }
}
```

### execution

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_mode` | string | `"ask"` | Default execution mode: ask/manual/auto |
| `auto_tdd` | boolean | `true` | Auto-use TDD |
| `task_granularity` | string | `"medium"` | Task granularity: fine/medium/coarse |

**default_mode:**
- `"ask"` - Ask every time (default)
- `"manual"` - Only generate plan, don't execute
- `"auto"` - Auto-execute tasks one by one

**task_granularity:**
- `"fine"` - Fine-grained, 5-10 tasks, 1-2 hours each
- `"medium"` - Medium-grained, 3-5 tasks, half day each
- `"coarse"` - Coarse-grained, 2-3 tasks, 1-2 days each

## Configuration File Location

### Priority (Highest to Lowest)

1. **Project Root** `.code-forge.json`
   - Highest priority
   - Project-specific configuration

2. **User Home Directory** `~/.code-forge.json`
   - Global default configuration
   - Applies to all projects

3. **Built-in Defaults**
   - Used if no configuration file exists

### Configuration Merging

If multiple configuration files exist, they are merged by priority:

```
Built-in defaults
  ← Override ← ~/.code-forge.json
  ← Override ← project/.code-forge.json
```

## Configuration Detection

When Forge starts, it will:

1. Check if `.code-forge.json` exists in project root
2. If exists, read and validate configuration
3. If invalid, display error and use defaults
4. Display current configuration being used

**Example Output:**
```
📋 Code Forge Configuration
├── Base directory: planning/
├── Input directory: planning/features/
├── Output directory: planning/implementation/
└── Configuration source: .code-forge.json (project)

Continue?
```

## Validate Configuration

After creating the configuration file, you can validate:

```bash
# Create configuration
cat > .code-forge.json <<'EOF'
{
  "directories": {
    "base": "dev-plans/"
  }
}
EOF

# Validate configuration (auto-validated when running Forge)
# Configuration is auto-validated when running any code-forge command
```

## Best Practices

### ✅ Commit `.code-forge.json` to Version Control

`.code-forge.json` **should be committed to Git**, similar to `.eslintrc.json` or `pyproject.toml`:
- Ensures all team members use the same planning directory structure
- The `_tool` section helps new members discover and install Code Forge
- Does not contain sensitive information

### ✅ Recommended Configuration

**Personal Project:**
```json
{
  "directories": {
    "base": "planning/",
    "input": "features/",
    "output": "implementation/"
  },
  "git": {
    "commit_state_file": false,
    "gitignore_patterns": ["**/state.json"]
  }
}
```

**Team Project:**
```json
{
  "directories": {
    "base": "planning/",
    "input": "features/",
    "output": "implementation/"
  },
  "git": {
    "commit_state_file": true,
    "gitignore_patterns": []
  }
}
```

### ❌ Not Recommended

```json
{
  // ❌ Don't use directories with tool names
  "directories": {
    "base": ".forge/",     // Tool traces
    "base": "claude-dev/"  // Tool traces
  },

  // ❌ Don't use existing directories
  "directories": {
    "base": "src/",        // May conflict
    "base": "node_modules/"  // Wrong
  }
}
```

## Migrate Existing Project

If you already used default configuration and want to migrate:

```bash
# 1. Create new configuration
cat > .code-forge.json <<'EOF'
{
  "directories": {
    "base": "dev-plans/"
  }
}
EOF

# 2. Move existing files
mv planning/ dev-plans/

# 3. Re-run Forge (will use new configuration)
/code-forge:plan @dev-plans/features/xxx.md
```

## Configuration Templates

Code Forge provides several preset templates:

```bash
# Copy template to project
cp /path/to/code-forge/templates/.code-forge.json .

# Or use presets
# Or manually edit from template
# Personal project: use minimal directories
# Team project: enable git.auto_commit and gitignore patterns
```

## Ignore Configuration File

If project has `.code-forge.json` but you want to temporarily ignore it:

```bash
/code-forge:plan @xxx.md --ignore-config
```

## Example: Avoid docs Conflict

**Scenario:** Project already has `docs/` for API documentation

**Solution 1: Use Separate Directory**
```json
{
  "directories": {
    "base": "planning/"
  }
}
```

**Solution 2: Use docs Subdirectory**
```json
{
  "directories": {
    "base": "docs/",
    "input": "feature-specs/",
    "output": "feature-plans/"
  }
}
```

**Result:**
```
project/
└── docs/
    ├── api/              # Existing API documentation
    ├── feature-specs/    # Forge input
    └── feature-plans/    # Forge output
```

## Summary

| Rating | Configuration | Use Case |
|--------|----------------|----------|
| ⭐⭐⭐ | `base: "planning/"` | Most projects, avoid conflict |
| ⭐⭐ | `base: "docs/..."` | Projects where docs/ doesn't conflict |
| ⭐ | `base: ".dev/"` | Don't want to see planning files |
| ❌ | `base: ".forge/"` | Tool traces, not recommended |
