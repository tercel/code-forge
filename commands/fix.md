---
description: "Use when fixing a bug — traces root cause across 4 levels and syncs upstream documents. Supports --repos for parallel multi-repo fixing."
argument-hint: "[\"bug description\" | @issue.md | --review [feature-name]] [--repos <repo1> <repo2> ...]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:fix skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
