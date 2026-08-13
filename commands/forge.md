---
description: "Smart dispatcher — routes any natural language input to the right code-forge skill, or shows help when invoked without arguments"
argument-hint: "<any natural language description of your task, or leave empty for help>"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

The user invoked `/code-forge:forge`.

## Branch on arguments

**If $ARGUMENTS is empty** — display the help menu below, then stop.

**If $ARGUMENTS is non-empty** — skip the help menu entirely. Go to **Intent Classification** below and execute the routed skill.

---

## Help Menu (no-args only)

```
Code Forge — Available Commands

Planning & Execution:
  /code-forge:plan @doc.md           Generate plan from a feature document
  /code-forge:plan @dir/             Browse a directory and pick a feature to plan
  /code-forge:plan "requirement"     Generate plan from a text prompt
  /code-forge:plan --tmp "req"       Generate plan in .code-forge/tmp/ (no project pollution)
  /code-forge:impl [feature]         Execute pending tasks for a feature
  /code-forge:impl feature --repos r1 r2
                                     Implement across multiple repos in parallel
  /code-forge:status [feature]       View dashboard or feature detail

Quality & Debugging:
  /code-forge:review [feature]       Review code quality for a feature or project
  /code-forge:review --feedback      Evaluate and respond to incoming review comments
  /code-forge:review --github-pr     Post 15-dimension review to a GitHub PR
  /code-forge:fix "description"      Debug and fix a bug with upstream trace-back
  /code-forge:fix --review           Batch-fix all issues from a review report
  /code-forge:fix "desc" --repos r1 r2
                                     Fix a bug across multiple repos in parallel
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

Tip: /code-forge:forge <anything>    Describe your task in plain language to auto-route
```

---

## Intent Classification

You have natural language input: **$ARGUMENTS**

Think about what the user is actually trying to accomplish before routing.

### Step 1 — Classify intent

Smart dispatch is scoped to **local, targeted problems**. Route only within the table below.

| Signal in input | Target skill | Extracted args |
|---|---|---|
| Bug / error / crash / failure / not working **in code** | `fix` | the description |
| Fix all review comments / batch fix issues | `fix --review` | feature name if mentioned |
| Why / root cause / investigate / how does X work | `debug` | the question |
| Implement / build / add / feature / requirement | `plan` | requirement description |
| Start implementing / continue / execute tasks | `impl` | feature name |
| Review a specific feature's **code** / check code quality | `review <feature>` | feature name — required |
| Respond to / evaluate incoming review feedback | `review --feedback` | — |
| TDD / test-driven / write tests first | `tdd` | — |
| Verify / is it done / check completion — settled by running a command | `verify` | — |
| Status / progress / dashboard | `status` | feature name if mentioned |

**Out of scope — do not route, redirect instead:**

| If input hints at... | Reply with |
|---|---|
| Full project-wide review | `Use /code-forge:review --project for a full project review.` |
| Post review to a GitHub PR | `Use /code-forge:review --github-pr <PR#> to post to a PR.` |
| Merge branch / create PR / finish branch | `Use /code-forge:finish to merge or create a PR.` |
| Port project to another language | `Use /code-forge:port to migrate the project language.` |
| Parallel agents / multi-repo execution | `Use /code-forge:parallel or add --repos to fix/impl.` |
| Create a worktree / isolated branch | `Use /code-forge:worktree <feature> to create an isolated git worktree.` |
| Review / audit a **document** (PRD, SRS, tech design, spec, README, paper, any .md) | `code-forge works on code. For document review use /spec-forge:review (specs/docs) or theory-forge (papers).` |
| Fix wording, typos, or content **inside a document** | `code-forge:fix fixes code defects. For document content use /spec-forge, or tell me the edit and I'll make it directly.` |
| Verify something no command can settle (a fact, a doc's accuracy, numbers) | `code-forge:verify runs verification commands. There is nothing to execute here — I'll check the source directly instead.` |
| A trivial mechanical edit (rename, format, constant bump) | `That's a direct edit — routing it through code-forge:fix would run a full root-cause + TDD cycle for no benefit. I'll just make the change.` |

**Ambiguous cases:**
- Feature request with no existing `.code-forge/` plan on disk → `plan`
- Feature request with an existing plan on disk → `impl`
- Bug + root-cause signals together → prefer `fix` (it includes diagnosis)
- Review signal with no feature name → ask which feature, do not default to project-wide

**No match — fallback:**

If after thinking you still cannot determine intent, ask one focused clarifying question rather than guessing a skill.

### Step 2 — Announce routing (one line)

Print exactly one line before executing, e.g.:
> Routing to `fix` — "login page returns 500 error"

### Step 3 — Invoke the target skill

Use the matching directive, substituting the description or feature name extracted in Step 1.

- `fix` → Invoke the code-forge:fix skill for '{extracted description}'.
- `fix --review` → Invoke the code-forge:fix skill for '--review {feature name}'.
- `debug` → Invoke the code-forge:debug skill for '{extracted question}'.
- `plan` → Invoke the code-forge:plan skill for '{extracted requirement}'.
- `impl` → Invoke the code-forge:impl skill for '{feature name}'.
- `review <feature>` → Invoke the code-forge:review skill for '{feature name}'.
- `review --feedback` → Invoke the code-forge:review skill for '--feedback'.
- `tdd` → Invoke the code-forge:tdd skill.
- `verify` → Invoke the code-forge:verify skill.
- `status` → Invoke the code-forge:status skill for '{feature name if any}'.
