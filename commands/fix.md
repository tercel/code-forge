---
description: "Use when fixing a bug in a code-forge tracked feature (has state.json) — traces root cause across 4 levels and syncs upstream plan/task documents"
argument-hint: "[\"bug description\" | @issue.md | --review [feature-name]]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:fix skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
