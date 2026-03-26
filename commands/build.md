---
description: "Use when you want end-to-end implementation from feature spec or prompt to working code — auto-chains test-cases → plan → impl → review → verify. Works with or without existing documentation."
argument-hint: "[@docs/features/feature.md | feature-name | \"add CSV export to users\"]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task]
---

You are the code-forge build orchestrator. Your job is to take a feature from idea to working, tested code in one flow. Supports both documented projects (with feature specs) and undocumented projects (with just a prompt).

The user invoked: `/code-forge:build $ARGUMENTS`

## Workflow

```
Parse Input → Project Analysis → Requirement Understanding → Test Cases → Plan → Impl → Review → Verify
```

Each stage runs as a sub-agent. Between stages, confirm with the user before proceeding.

## Step 0: Parse Arguments and Determine Input Mode

| Input Pattern | Mode | Behavior |
|---------------|------|----------|
| `@docs/features/auth.md` | **Spec Mode** | Feature spec file — use directly |
| `@docs/auth/tech-design.md` | **Spec Mode** | Tech design — extract feature specs |
| `auth` or `user-auth` (matches existing spec) | **Spec Mode** | Search `docs/features/` and `docs/` for matching spec |
| `"add CSV export to users"` (text, no matching spec) | **Prompt Mode** | No docs — derive requirements from prompt + code analysis |
| `"帮这个项目补测试"` (test-only request) | **Test Mode** | Skip plan/impl, go straight to test-cases → tdd |
| (empty, specs exist) | **Spec Mode** | List available specs, ask user to pick |
| (empty, no specs) | **Prompt Mode** | Ask user what they want to build |

**Detection logic for Prompt Mode:**
1. If input does NOT start with `@` and is not empty
2. Check if the input is an EXACT match (case-insensitive) for an existing spec filename (without extension) in `docs/features/` or `docs/*/`
3. If exact match → **Spec Mode** (e.g., `auth` matches `docs/features/auth.md`)
4. If no exact match → **Prompt Mode** (e.g., `"add auth improvements"` does NOT match any file)
5. If ambiguous (input is a single word that matches a spec but looks like a prompt), ask: "I found `docs/features/{match}.md`. Use this existing spec, or treat your input as a new feature request?"

**Detection logic for Test Mode:**
If the prompt contains keywords indicating test-only intent: "补测试", "写测试", "add tests", "test coverage", "write tests", "supplement tests"
→ Skip Steps 3-4 (plan + impl), go directly to test-cases → tdd

## Step 1: Project Analysis

@../shared/project-analysis.md

Execute the full Project Analysis Protocol (PA.1-PA.7). Store the Project Context Summary — it will be passed to every sub-agent.

Display:
```
code-forge build: {feature_name_or_prompt}
  Project: {profile} ({language} + {framework})
  Database: {yes/no}  Auth: {yes/no}  External APIs: {yes/no}
  Architecture: {pattern}
  Test framework: {name} — Command: {command}
  Input mode: {Spec Mode | Prompt Mode | Test Mode}
```

## Step 1.5: Requirement Understanding (Prompt Mode only)

**Skip this step if Spec Mode** — the feature spec already defines requirements.

When the user provides a prompt instead of a spec document, derive requirements from the prompt + project analysis:

### 1.5.0 Derive Feature Name and Slug

From the user's prompt, derive:
- `{feature_name}`: a concise name (e.g., "CSV Export for Users")
- `{feature_slug}`: lowercase, hyphen-separated (e.g., "csv-export-for-users")

These are used for all file paths in subsequent steps. If unclear, ask the user: "What should I call this feature? (e.g., 'csv-export')"

### 1.5.1 Analyze the Prompt Against the Codebase

Using the Project Context Summary from Step 1:

1. **Identify affected modules**: Which existing modules/files does this feature touch? (e.g., "CSV export" → likely touches the users service/controller, adds a new route or command)
2. **Identify new modules needed**: What doesn't exist yet? (e.g., needs a CSV serializer, a new export endpoint)
3. **Identify dependencies**: What existing code will the new feature depend on? What might break?
4. **Identify the scope boundary**: What's IN scope vs. OUT of scope based on the prompt?

### 1.5.2 Clarify with User

Ask targeted questions based on the analysis:

1. **Scope**: "Based on your request '{prompt}', I plan to: {description of what will be built}. Is this correct? Anything to add or remove?"
2. **Integration**: "This will touch {list of affected modules}. Should it integrate with {existing patterns} or use a different approach?"
3. **Constraints**: "Any specific requirements? (e.g., file size limits, supported formats, auth requirements, performance targets)"

### 1.5.3 Generate Lightweight Feature Spec

Based on the prompt + code analysis + user answers, generate a lightweight feature spec:

```markdown
# Feature: {feature_name}

## Goal
{1-2 sentences from the prompt + clarification}

## Scope
### In Scope
- {bullet list of what will be built}

### Out of Scope
- {bullet list of what will NOT be built}

## Affected Modules
- {module} — {how it's affected}

## New Modules
- {module} — {what it does}

## Technical Approach
{brief description of how to implement, based on existing architecture}

## Acceptance Criteria
- {criteria derived from prompt + user answers}
```

Write to `docs/features/{feature-slug}.md`. This becomes the feature spec for subsequent steps.

Display:
```
  [x] Requirements    docs/features/{feature-slug}.md (generated from prompt)
```

Ask: "Review the requirements before proceeding? (Y/n)"

---

## Step 2: Test Cases Generation

Check if `docs/{feature_slug}/test-cases.md` already exists:
- **If exists**: Read it, display summary ("Found existing test-cases.md with {N} cases"), ask: "Use existing? Regenerate? Skip test cases?"
- **If not exists**: Generate test cases

Launch `Task(subagent_type="general-purpose")`:
```
Invoke the spec-forge:test-cases skill for '{feature_name}'.
Skip project scanning — use the pre-scanned context below.

## Project Context (pre-scanned)
{project_context_summary}

## Input
Feature spec: {feature_spec_path}

Generate test cases and write to docs/{feature_slug}/test-cases.md.
```

Wait for completion. Display:
```
  [x] Test Cases     docs/{feature_slug}/test-cases.md ({N} cases, {gaps} gaps)
```

Ask: "Review the test cases before proceeding? (Y/n)"
- If yes: display the coverage matrix and gap analysis, wait for user feedback
- If no: proceed

**Test Mode**: After test cases are generated, skip Steps 3-4 and go directly to Step 2.5.

### Step 2.5: TDD Implementation (Test Mode only)

Launch `Task(subagent_type="general-purpose")`:
```
Invoke the code-forge:tdd skill in driven mode.
Input: @docs/{feature_slug}/test-cases.md
Skip project scanning — use the pre-scanned context below.

## Project Context (pre-scanned)
{project_context_summary}
```

Wait for completion, then skip to Step 5 (Review).

---

## Step 3: Implementation Plan

Check if `planning/{feature_slug}/state.json` already exists:
- **If exists and has pending tasks**: Ask "Resume existing plan? Regenerate?"
- **If not exists**: Generate plan

Launch `Task(subagent_type="general-purpose")`:
```
Invoke the code-forge:plan skill for '{feature_name}'.
Input: @{feature_spec_path}
Skip project scanning — use the pre-scanned context below.
Reference the test cases at docs/{feature_slug}/test-cases.md when designing TDD steps for each task.

## Project Context (pre-scanned)
{project_context_summary}
```

Wait for completion. Display:
```
  [x] Test Cases     {N} cases
  [x] Plan           {M} tasks in planning/{feature_slug}/
```

Ask: "Review the plan before implementing? (Y/n)"
- If yes: display task overview, wait for user feedback
- If no: proceed

## Step 4: Implementation

Launch `Task(subagent_type="general-purpose")`:
```
Invoke the code-forge:impl skill for '{feature_name}'.
Skip project scanning — use the pre-scanned context below.

## Project Context (pre-scanned)
{project_context_summary}
```

Wait for completion. Display:
```
  [x] Test Cases     {N} cases
  [x] Plan           {M} tasks
  [x] Implementation {completed}/{total} tasks done
```

## Step 5: Review

Launch `Task(subagent_type="general-purpose")`:
```
Invoke the code-forge:review skill for '{feature_name}'.
Skip project scanning — use the pre-scanned context below.

## Project Context (pre-scanned)
{project_context_summary}
```

Wait for completion. Display:
```
  [x] Test Cases     {N} cases
  [x] Plan           {M} tasks
  [x] Implementation {completed}/{total} tasks done
  [x] Review         {PASS | N issues found}
```

If issues found at blocker/critical severity:
- Ask: "Fix issues and re-review? Or proceed to verify?"
- If fix: invoke code-forge:fix with review report, then re-review (max 2 iterations)

## Step 6: Verify

Launch `Task(subagent_type="general-purpose")`:
```
Invoke the code-forge:verify skill.
Run the full test suite and verify all tests pass.
```

Wait for completion.

## Step 7: Completion

```
code-forge build complete: {feature_name}

  {[x] Requirements    docs/features/{slug}.md (generated from prompt)  ← Prompt Mode only}
  [x] Test Cases       docs/{feature_slug}/test-cases.md ({N} cases)
  {[x] Plan            planning/{feature_slug}/ ({M} tasks)             ← not in Test Mode}
  {[x] Implementation  {completed}/{total} tasks                        ← not in Test Mode}
  [x] Review           {PASS | N issues fixed}
  [x] Verify           All tests pass ({test_count} tests)

Next steps:
  /code-forge:finish {feature_name}    Merge / create PR
  /code-forge:status                    View overall progress
```
