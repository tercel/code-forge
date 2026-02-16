---
description: "Show available code-forge commands"
allowed-tools: [Read, Glob, Grep]
---

The user invoked `/code-forge:forge`. This is a legacy entry point.

**Do not route or parse subcommands.** Instead, display the available commands:

```
Code Forge — Available Commands

  /code-forge:plan @doc.md           Generate plan from a feature document
  /code-forge:plan @dir/             Browse a directory and pick a feature to plan
  /code-forge:plan "requirement"     Generate plan from a text prompt
  /code-forge:impl [feature]         Execute pending tasks for a feature
  /code-forge:status [feature]       View dashboard or feature detail
  /code-forge:fixbug "description"   Debug and fix a bug with upstream trace-back
  /code-forge:review [feature]       Review code quality for a feature
  /code-forge:port @docs --ref impl --lang java
                                     Port a project to a new language
```

If the user provided arguments ($ARGUMENTS), suggest the correct command. For example:
- `fixbug "some bug"` → suggest `/code-forge:fixbug "some bug"`
- `plan @file.md` → suggest `/code-forge:plan @file.md`
- `impl feature` → suggest `/code-forge:impl feature`
- (no args) → suggest `/code-forge:status`
