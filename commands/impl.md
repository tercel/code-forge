---
description: "Use when implementing a feature — executes TDD tasks via sub-agents with state tracking and auto-resume. Supports --repos for parallel multi-repo implementation."
argument-hint: "[feature-name] [--repos <repo1> <repo2> ...]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

Invoke the code-forge:impl skill and follow it exactly as presented to you.

The user invoked this command with: $ARGUMENTS
