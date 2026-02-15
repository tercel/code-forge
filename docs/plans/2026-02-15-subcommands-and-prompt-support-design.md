# Code-Forge: Subcommand Architecture & Prompt Support

**Date:** 2026-02-15
**Status:** Approved
**Version:** 0.4.0 → 0.5.0 (breaking change)

## Overview

Two enhancements to code-forge:

1. **Prompt support** — `/forge 实现用户登录功能` directly passes requirement text, auto-generates a feature document, then follows the standard planning flow.
2. **Subcommand architecture** — Split the monolithic `forge/SKILL.md` into 5 independent skills (`plan`, `impl`, `status`, `fixbug`, `review`), routed through a rewritten `forge.md` orchestrator. Follows the spec-forge subcommand pattern.

## Architecture

### File Structure (After)

```
code-forge/
├── commands/
│   ├── forge.md           ← Main router (rewritten)
│   ├── plan.md            ← /forge:plan alias
│   ├── impl.md            ← /forge:impl alias
│   ├── status.md          ← /forge:status alias
│   ├── fixbug.md          ← /forge:fixbug alias
│   └── review.md          ← /forge:review alias
├── skills/
│   ├── plan/SKILL.md      ← Step 0, 0.8(new), 1-9
│   ├── impl/SKILL.md      ← Step 0, 10-12
│   ├── status/SKILL.md    ← Step 0, 0.7, 8.5
│   ├── fixbug/SKILL.md    ← New: debugging workflow
│   └── review/SKILL.md    ← New: code review workflow
├── docs/
├── examples/
├── templates/
└── README.md
```

The old `skills/forge/SKILL.md` is deleted.

### Router (forge.md)

The main command is rewritten as an orchestrator that parses arguments and routes to subcommands.

**Argument parsing rules:**

```
$ARGUMENTS parsing:

1. Empty              → subcommand = "status"
2. First word is known subcommand (plan/impl/status/fixbug/review)
                      → subcommand = that word, remaining = args
3. First word starts with @
                      → subcommand = "plan", args = entire $ARGUMENTS
4. Other text         → subcommand = "plan", args = entire $ARGUMENTS (prompt mode)
```

**Routing table:**

| Input | subcommand | args | Action |
|-------|-----------|------|--------|
| `/forge plan @file.md` | `plan` | `@file.md` | Analyze doc, generate plan |
| `/forge plan 实现用户登录` | `plan` | prompt text | Auto-gen doc, then plan |
| `/forge impl user-auth` | `impl` | `user-auth` | Execute pending tasks |
| `/forge status` | `status` | — | Project dashboard |
| `/forge status user-auth` | `status` | `user-auth` | Feature detail |
| `/forge fixbug 描述` | `fixbug` | bug description | Debug workflow |
| `/forge review user-auth` | `review` | `user-auth` | Code review |
| `/forge @file.md` | `plan` | `@file.md` | **Backward compat** |
| `/forge 实现用户登录` | `plan` | prompt text | **New feature** |
| `/forge` | `status` | — | Dashboard |

**Routing action:** Each subcommand invokes the corresponding `code-forge:{subcommand}` skill with args.

### Subcommand Alias Files (commands/*.md)

Each subcommand has a thin alias file:

```yaml
---
description: "<subcommand description>"
argument-hint: "<hint>"
allowed-tools: [...]
---

Invoke the code-forge:<subcommand> skill and follow it exactly.

The user invoked this command with: $ARGUMENTS
```

Argument hints per subcommand:

| Command | argument-hint |
|---------|--------------|
| plan | `[@feature-doc.md \| "requirement description"]` |
| impl | `[feature-name]` |
| status | `[feature-name]` |
| fixbug | `["bug description" \| @issue.md]` |
| review | `[feature-name]` |

## Feature 1: Prompt Support

### Input Type Detection (in plan skill)

```
$ARGUMENTS arrives at plan skill
  ├── Starts with @  → file path mode → existing Step 1 (validate file)
  └── Other text     → prompt mode    → new Step 0.8 (auto-generate doc)
```

### New Step 0.8: Prompt to Document

Inserted between Step 0 (config loading) and Step 1 (validate document):

1. Convert prompt text to kebab-case slug
   - For non-ASCII text (Chinese, etc.): use `AskUserQuestion` to let user confirm or customize the slug
2. Check if `{input_dir}/{slug}.md` already exists
   - Exists → ask: append / overwrite / use existing?
   - Not exists → continue
3. Generate minimal feature document at `{input_dir}/{slug}.md`:
   ```markdown
   # {Feature Title}

   ## Requirements

   {user's original prompt text}

   ## Notes

   - Generated from prompt by code-forge
   - Created: {ISO timestamp}
   ```
4. Set file path as current input, continue to Step 1

**Design principles:**
- Document is minimal — only wraps the user's original text, no AI expansion
- Expansion happens in Step 2 (sub-agent analysis) as normal
- All subsequent steps see a standard `@file.md`, unaware of input source

## Feature 2: Subcommand Skill Breakdown

### plan/SKILL.md — Analysis & Plan Generation

Inherits from the original SKILL.md with adjustments:

| Step | Content | Change |
|------|---------|--------|
| Step 0 | Config detection & loading | Unchanged |
| Step 0.8 | Prompt to document | **New** (prompt mode only) |
| Step 1 | Validate input document | Unchanged |
| Step 2 | Analyze document (sub-agent) | Unchanged |
| Step 3 | Clarification questions | Unchanged |
| Step 4 | Create directory structure | Unchanged |
| Step 6 | Generate plan.md (sub-agent) | Unchanged |
| Step 7 | Task breakdown (sub-agent) | Unchanged |
| Step 5 | Generate overview.md | Unchanged (still after 6/7) |
| Step 8 | Initialize state.json | Unchanged |
| Step 8.5 | Project-level overview | Unchanged |
| Step 9 | Display plan summary | Adjusted: suggest `/forge impl {feature}` |

Does **not** include Step 10-12. Ends with next-step guidance.

### impl/SKILL.md — Task Execution

| Step | Content | Change |
|------|---------|--------|
| Step 0 | Config detection & loading | Reused |
| Locate feature | Find `{output_dir}/{feature}/state.json` | **New**: no args → list executable features |
| Step 10 | Confirm execution method | Unchanged |
| Step 11 | Task execution loop (sub-agents) | Unchanged |
| Step 11.5 | Verify generated files | Unchanged |
| Step 12 | Completion summary | Adjusted: suggest `/forge review {feature}` |

### status/SKILL.md — Dashboard & Progress

| Step | Content | Source |
|------|---------|--------|
| Step 0 | Config detection & loading | Reused |
| Global dashboard | Scan all features, display progress table | From original Step 0.7 |
| Single feature detail | Display task list and status for a feature | **New** |
| Project overview update | Regenerate `{output_dir}/overview.md` | From original Step 8.5 |

Args: `/forge status` → global; `/forge status user-auth` → feature detail.

### fixbug/SKILL.md — Bug Debugging Workflow (New)

Interactive trace-back debugging with upstream document synchronization:

```
Step 1: Receive bug description (prompt text or @issue-file.md)

Step 2: Project context scan
  - Load config (reuse Step 0)
  - Scan codebase, locate related files

Step 3: Associate feature (if exists)
  - Search {output_dir}/*/state.json
  - Match feature by affected files
  - Found → load plan.md + task files as context
  - Not found → mark as standalone bug, skip upstream trace

Step 4: Root cause diagnosis
  - Reproduce → locate root cause
  - Classify root cause level:
    Level 1: Code bug (logic error, boundary miss)
    Level 2: Incomplete task description (task.md steps missing)
    Level 3: Plan design flaw (plan.md architecture issue)
    Level 4: Incomplete requirement doc (original feature doc)

Step 5: Interactive trace-back confirmation (core)
  - Present root cause analysis and level to user
  - If Level >= 2, ask per level:
    AskUserQuestion: "Root cause traced to {level}, update this document?"
      - "Yes, update" → mark for update
      - "No, code fix only" → skip this level
      - "Show diff" → display current doc vs proposed correction
  - Generate fix plan: code fix + upstream doc correction checklist

Step 6: TDD fix
  - Write regression test → implement fix → verify passing

Step 7: Upstream document sync (based on Step 5 confirmations)
  - Level 2 confirmed → modify corresponding task.md
  - Level 3 confirmed → modify plan.md relevant sections
  - Level 4 confirmed → modify original feature document
  - Show diff preview before each modification

Step 8: Update state.json
  - Record fix: bug description, root cause level, fixed files, associated commits
  - If upstream docs modified, record in doc_updates field

Step 9: Summary
  - Fix content + root cause analysis + document update log
  - Regression test coverage confirmation
```

### review/SKILL.md — Code Review Workflow (New)

```
Step 1: Locate feature (args → state.json)

Step 2: Collect change scope
  - Extract all commits from state.json tasks[].commits
  - git diff for complete changes

Step 3: Review dimensions
  - Code quality (naming, structure, complexity)
  - Test coverage (all tasks have tests?)
  - Security (OWASP top 10 check)
  - Consistency with original plan.md

Step 4: Generate review report → {output_dir}/{feature}/review.md

Step 5: Update state.json (add review status)

Step 6: Summary + suggest next steps (fix issues / create PR)
```

### Shared Logic: Step 0 Config Loading

Each skill file **inlines** the full Step 0 config loading logic. Rationale:
- Skill files are loaded independently, cannot import shared modules
- Consistent with spec-forge's approach
- Config loading is only ~1.5KB, duplication cost is low

## Migration

### Breaking Changes

- `skills/forge/SKILL.md` deleted — `/forge:forge` no longer works
- Users should use `/forge plan`, `/forge impl`, etc.
- Version bump: 0.4.0 → 0.5.0

### Backward Compatibility

| Old usage | New behavior | User perception |
|-----------|-------------|----------------|
| `/forge` | Routes to `status` | Dashboard unchanged |
| `/forge @file.md` | Routes to `plan`, file mode | Identical |
| `/forge:forge` | **Removed** | Must use `/forge plan` |

### plugin.json Update

```json
{
  "name": "code-forge",
  "description": "Forge executable, TDD-driven implementation plans from documentation — with subcommands for planning, execution, debugging, and review",
  "version": "0.5.0"
}
```

## Allowed Tools per Skill

| Skill | Special tools | Reason |
|-------|--------------|--------|
| plan | Task (sub-agents Step 2/6/7) | Document analysis and plan generation |
| impl | Task (sub-agents Step 11) | Task execution |
| status | No Task needed | Read-only, lightest weight |
| fixbug | Task, Bash | Run tests, reproduce bugs |
| review | Task, Bash | git diff, run tests |

## Usage Examples (for README)

```
/forge                              → Dashboard (all features)
/forge plan @docs/feature.md        → Generate plan from document
/forge plan 实现用户登录功能          → Generate plan from prompt
/forge impl user-auth               → Execute pending tasks
/forge status                       → Project dashboard
/forge status user-auth             → Feature detail
/forge fixbug 登录页面报500错误       → Debug workflow
/forge review user-auth             → Code review

Aliases: /forge:plan, /forge:impl, /forge:status, /forge:fixbug, /forge:review
```
