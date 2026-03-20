---
description: "Show all code-forge commands and usage guide"
allowed-tools: [Read, Glob, Grep]
---

The user invoked `/code-forge:forge`. This is a legacy entry point.

**Do not route or parse subcommands.** Instead, display the available commands:

```
Code Forge — Available Commands

Planning & Execution:
  /code-forge:plan @doc.md           Generate plan from a feature document
  /code-forge:plan @dir/             Browse a directory and pick a feature to plan
  /code-forge:plan "requirement"     Generate plan from a text prompt
  /code-forge:plan --tmp "req"       Generate plan in .code-forge/tmp/ (no project pollution)
  /code-forge:impl [feature]         Execute pending tasks for a feature
  /code-forge:status [feature]       View dashboard or feature detail

Quality & Debugging:
  /code-forge:review [feature]       Review code quality for a feature or project
  /code-forge:review --feedback      Evaluate and respond to incoming review comments
  /code-forge:review --github-pr     Post 14-dimension review to a GitHub PR
  /code-forge:fix "description"      Debug and fix a bug with upstream trace-back
  /code-forge:fix --review           Batch-fix all issues from a review report
  /code-forge:debug "description"    Systematic root cause debugging (general-purpose)

Development Methodology:
  /code-forge:tdd                    Enforce Red-Green-Refactor cycle (standalone TDD)
  /code-forge:verify                 Verify work before claiming completion

Workspace & Branch Lifecycle:
  /code-forge:worktree <feature>     Create isolated git worktree with project setup
  /code-forge:finish                 Merge, PR, keep, or discard a completed branch

Advanced:
  /code-forge:parallel               Dispatch parallel agents for independent problems
  /code-forge:port @docs --ref impl --lang java
                                     Port a project to a new language
```

If the user provided arguments ($ARGUMENTS), suggest the correct command. For example:
- `fix "some bug"` → suggest `/code-forge:fix "some bug"`
- `fix --review` → suggest `/code-forge:fix --review`
- `plan @file.md` → suggest `/code-forge:plan @file.md`
- `impl feature` → suggest `/code-forge:impl feature`
- `debug "error"` → suggest `/code-forge:debug "error"`
- `worktree feat` → suggest `/code-forge:worktree feat`
- `tdd` → suggest `/code-forge:tdd`
- `verify` → suggest `/code-forge:verify`
- `finish` → suggest `/code-forge:finish`
- `parallel` → suggest `/code-forge:parallel`
- `review --feedback` → suggest `/code-forge:review --feedback`
- `review --github-pr` → suggest `/code-forge:review --github-pr`
- `review --github-pr 123` → suggest `/code-forge:review --github-pr 123`
- (no args) → suggest `/code-forge:status`
