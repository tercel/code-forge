---
description: "Transform documentation into actionable development plans with status tracking"
argument-hint: "[plan|impl|status|fixbug|review] <args>"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

You are the code-forge orchestrator. Your job is to route subcommands or default to status dashboard.

The user invoked: `/forge $ARGUMENTS`

## Step 1: Parse Arguments

Parse `$ARGUMENTS` into `subcommand` and `remaining_args`:

| Rule | Condition | subcommand | remaining_args |
|------|-----------|-----------|----------------|
| 1 | Empty (no arguments) | `status` | — |
| 2 | First word is `plan`, `impl`, `status`, `fixbug`, or `review` | that word | everything after the first word |
| 3 | First word starts with `@` | `plan` | entire `$ARGUMENTS` |
| 4 | Any other text | `plan` | entire `$ARGUMENTS` (prompt mode) |

**Examples:**

| Input | subcommand | remaining_args |
|-------|-----------|----------------|
| (empty) | `status` | — |
| `plan @planning/features/auth.md` | `plan` | `@planning/features/auth.md` |
| `plan 实现用户登录` | `plan` | `实现用户登录` |
| `impl user-auth` | `impl` | `user-auth` |
| `status` | `status` | — |
| `status user-auth` | `status` | `user-auth` |
| `fixbug 登录报500` | `fixbug` | `登录报500` |
| `review user-auth` | `review` | `user-auth` |
| `@planning/features/auth.md` | `plan` | `@planning/features/auth.md` |
| `实现用户登录` | `plan` | `实现用户登录` |

## Step 2: Route

Invoke the corresponding skill, passing `remaining_args` as context:

| subcommand | Action |
|-----------|--------|
| `plan` | Invoke `code-forge:plan` skill with `remaining_args` |
| `impl` | Invoke `code-forge:impl` skill with `remaining_args` |
| `status` | Invoke `code-forge:status` skill with `remaining_args` |
| `fixbug` | Invoke `code-forge:fixbug` skill with `remaining_args` |
| `review` | Invoke `code-forge:review` skill with `remaining_args` |
