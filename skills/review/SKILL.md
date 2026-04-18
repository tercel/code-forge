---
name: review
description: >
  Use when reviewing code, handling review feedback, or posting a review to a GitHub PR —
  15-dimension quality analysis for features or entire projects (generate mode), structured
  evaluation and response to incoming review comments (feedback mode via --feedback flag),
  or automated PR review posted as a GitHub comment (--github-pr flag).
---

# Code Forge — Review

## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read Step 1 (Determine Review Mode), perform it, then Step 2, etc., until the workflow completes or you reach an `AskUserQuestion` checkpoint.

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual review", "回退到手动 review", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to Step 1 of the Detailed Steps and start executing.

The first user-visible action of this skill should be either (a) the output of Step 1 / Step 2 of the workflow, or (b) an `AskUserQuestion` if Step 1 needs disambiguation. Never an apology, never a fallback, never silence.

---

Comprehensive code review against reference documents and engineering best practices. Covers functional correctness, security, resource management, code quality, architecture, performance, testing, error handling, observability, maintainability, backward compatibility, and dependency safety.

Supports four modes:
- **Feature mode:** Review a single feature against its `plan.md`
- **Project mode:** Review the entire project against planning documents or upstream docs
- **Feedback mode:** Evaluate and respond to incoming code review comments (`--feedback`)
- **GitHub PR mode:** Post a 15-dimension review as a comment on a GitHub PR (`--github-pr`)

## When to Use

- Feature implementation is complete or nearly complete
- Want to verify code quality before creating a PR
- Need a structured review against the original plan or documentation
- Want a holistic project-level quality check
- Received code review feedback and need to evaluate/respond to it (`--feedback`)
- Want to post a code review directly to a GitHub PR for team visibility (`--github-pr`)

## Examples

```bash
/code-forge:review user-auth             # Review a specific feature
/code-forge:review --project             # Full project review
/code-forge:review                       # Auto-detect features to review
/code-forge:review --feedback            # Evaluate incoming review comments
/code-forge:review --github-pr 123       # Post review to GitHub PR #123
/code-forge:review user-auth --save      # Review and save report to disk
```

## Workflow

```
Config → Determine Mode → Locate Reference → Collect Scope → Multi-Dimension Review (sub-agent) → Display Report → Update State → Summary
```

## Context Management

The review analysis is offloaded to a sub-agent to handle large diffs without exhausting the main context.

## Project Analysis

Before reviewing code, understand the project's architecture and tech stack:

@../shared/project-analysis.md

Execute PA.1 (Project Profile) and PA.2 (Architecture Analysis). This informs:
- Which review dimensions apply (D14 Accessibility only for frontend)
- Language-specific checks (Rust `unsafe` blocks, Go unchecked errors, Python type hints)
- Architecture-specific checks (layer boundary violations, circular dependencies)
- The Project Profile determines which patterns are expected vs. suspicious

## Review Severity Levels

All issues use a 4-tier severity system, ordered by merge-blocking priority:

| Severity     | Symbol | Meaning                                               | Merge Policy            |
|--------------|--------|-------------------------------------------------------|-------------------------|
| `blocker`    | :no_entry:     | Production risk. Data loss, security breach, crash.   | **Must fix before merge** |
| `critical`   | :warning:     | Significant quality/correctness concern.              | **Must fix before merge** |
| `warning`    | :large_orange_diamond:     | Recommended fix. Could cause issues over time.        | Should fix              |
| `suggestion` | :blue_book:     | Nice-to-have improvement. Can address later.          | Nice-to-have            |

## Call-Graph Discipline (Mandatory Pre-Analysis)

**Before applying any dimension, the review sub-agent MUST build a call graph for every public method in the review scope.** This is a procedural requirement, not a new dimension. It exists because surface-level reading of a method body is structurally blind to a class of bugs: a method may look complete, have the right signature, match the declared plan/spec, yet silently skip a validation call, lack a null-guard on external input, or omit an expected state mutation. These bugs are visible in the call graph and invisible in the method body alone.

**The graph must enumerate, for every public method:**
1. **Every step in the execution path — including steps inside private helpers called from the public method.** When a public method calls a private helper defined in the same reviewed scope (same file, or a nearby private module within the review set), you MUST open that helper and **inline its steps** (validations, mutations, raises, iterates, subscripts, calls-to-further-helpers) into the public method's chain. Do NOT leave a private same-scope helper as an opaque `call` step — that hides exactly the bugs this discipline exists to catch (a public method `discover` whose private helper `_discover_custom` silently indexes `entry["module_id"]` without a KeyError guard is invisible if you stop expansion at the `call` boundary).
2. **Leaves of the graph are ONLY:** stdlib calls, third-party library calls, framework calls, or private helpers that live in a different module NOT currently in the reviewed file set. Represent these as `ext_call` steps with no further expansion.
3. **Every validation performed anywhere in the chain** (early `if/raise`, `assert`, `match`, type guards, schema validation, Protocol checks, `isinstance`, `instanceof`) — including validations inside inlined private helpers.
4. **Every state mutation anywhere in the chain** (writes to `self.x` / `this.x`, inserts into maps/sets/lists, event emissions, lock acquisitions, external I/O) — including mutations inside inlined private helpers.
5. **Every error raised anywhere in the chain** (`raise`, `throw`, `return Err`, `return nil, err`) — including raises inside inlined private helpers.
6. **Every external input path anywhere in the chain** (iteration over arguments, subscript/indexing into external data — especially data returned by plugin/discoverer/factory callbacks, deserialization of user/plugin/config input, network reads) — including paths inside inlined private helpers. This is where defensive-gap bugs live and they are almost always inside private helpers.

**Inlining convention.** When inlining a private helper's steps into a public method's chain, prefix the `detail` field with the helper name for traceability, e.g.:

```
- { kind: call,      detail: "_discover_custom(rootPaths)", line: 257 }
- { kind: call,      detail: "  _discover_custom → custom_discoverer.discover(roots)", line: 262 }
- { kind: iterate,   detail: "  _discover_custom → for entry in custom_modules", line: 263 }
- { kind: subscript, detail: "  _discover_custom → entry['module_id']  (unguarded, KeyError crashes loop)", line: 269 }
```

The indentation + `helper_name →` prefix preserves the call hierarchy without needing a separate nested-list structure. The reviewer who reads the chain can tell at a glance which step is rooted where.

**The graph is produced as structured output (see `references/sub-agent-format.md` `METHOD_CHAINS` section)** — the sub-agent shows its work. An empty or missing `METHOD_CHAINS` section means the sub-agent skipped the pre-analysis; the orchestrator MUST reject the report and re-run.

**Why this is procedural, not a dimension.** The graph is an *input* to dimensions D1 (correctness), D3 (resource), D8 (error handling), D15 (anti-bloat), and others — not a finding category itself. Dimensions are applied to the graph, not to the raw method body. Findings that emerge from graph inspection still belong to their natural dimension (e.g., "method skips a validation its docstring promises" → D1; "method exits without releasing a lock it acquired" → D3).

**Scope.** The discipline applies to **every public method of every class, every exported function, and every entry-point / CLI command** in the reviewed files. Private helpers do NOT get their own top-level `METHOD_CHAINS` entry — but their steps (validations, mutations, raises, iterates, subscripts) MUST be inlined into the chain of the public method that invokes them, using the inlining convention above. Stopping expansion at `call: _private_helper` without inlining its body is a **pre-analysis failure**; the orchestrator rejects such chains. Test files are exempt.

**Anti-rationalization:**

| Thought | Reality |
|---------|---------|
| "The method is only 10 lines, the graph is trivial, skip it" | The Rust `discover_internal` bug in apcore-rust was in a short method. Short methods that skip expected work are exactly what the graph catches — the absence of a call is invisible to surface reading. Always build the graph. |
| "The plan / spec says the method does X, so it does X" | Do not trust the plan. Verify X is actually invoked by reading the chain to its leaves. A common skill-driven bug: the plan says "implement validate_module_id", the impl file adds a `validate_module_id` function, but no caller ever invokes it. |
| "The method calls a well-named helper, the helper must be doing its job" | Never infer behavior from function names. Open the helper and verify. A helper called `validate_foo()` may be a stub, may early-return on a wrong branch, may not actually validate. |
| "This is defensive code for impossible states, D15 says flag it as suggestion" | D15 targets defensive code for states that the type system or upstream invariant actually prevents. Defensive code for **possible** states — external-facing iteration, subscript into user/plugin-supplied dicts, deserialization paths — is D1 territory (functional correctness). Do not downgrade to suggestion when the input source is genuinely external. |
| "No reference document, can't check purpose" | In bare mode you cannot check against a spec, but you can still check **internal consistency**: does the method name imply a contract (`discover`, `register`, `validate`) that the chain contradicts? Does the public API promise a return shape that the chain does not produce? Graph inspection still yields signal. |
| "The public method just calls `_private_helper()` — that's one `call` step, chain done" | NO. The most common place for defensive-gap bugs and missing-validation bugs is **inside private helpers** — a public method with a clean three-line body whose private helper does an unguarded subscript into plugin output, or an iterate over possibly-null external data, is the exact case this discipline exists to catch. When a `call` targets a private helper defined in the same reviewed scope, you MUST open it and inline its steps per the inlining convention. "Stop at the first `call` boundary" produces the illusion of a clean chain while the bug hides one level deeper. If your METHOD_CHAINS for a public method is ≤3 steps because its body was "just delegation", you almost certainly skipped inlining — go back and expand. |

## Review Dimensions Reference

For the full list of 15 review dimensions with check items, read `references/dimensions.md`.

**Quick summary by tier:**
- **Tier 1 (Must-Fix):** D1 Functional Correctness, D2 Security, D3 Resource Management
- **Tier 2 (Should-Fix):** D4 Code Quality, D5 Architecture, D6 Performance, **D15 Simplification & Anti-Bloat**, D7 Test Coverage
- **Tier 3 (Recommended):** D8 Error Handling, D9 Observability, D10 Standards
- **Tier 4 (Nice-to-Have):** D11 Backward Compat, D12 Maintainability, D13 Dependencies, D14 Accessibility (frontend only)

**Dimension Application Rules:**
- **D1–D3:** Always apply. Potential merge blockers.
- **D4–D7, D15:** Always apply. Should-fix items.
- **D8–D10:** Always apply. Flag as warnings/suggestions.
- **D11–D13:** Always apply but expect mostly suggestions.
- **D14:** Apply ONLY if `project_type` is `"frontend"` or `"fullstack"`.
- **D15 (Simplification & Anti-Bloat):** Always apply. Mandatory in every mode (feature, project, GitHub PR). This is the primary defense against incremental bloat from skill-driven workflows — sub-agents MUST grep for existing equivalents before accepting any new symbol, MUST verify external callers exist for every new top-level symbol, and MUST flag scope creep beyond `plan.md`. Never skip D15 even on small changes.

When spawning review sub-agents, instruct them to read `references/dimensions.md` for the full check items.

---

## Detailed Steps

@../shared/configuration.md

---

### Step 1: Determine Review Mode

Parse the user's arguments to determine which mode to use.

#### 1.0a `--github-pr` Flag Provided

If the user passed `--github-pr` (e.g., `/code-forge:review --github-pr` or `/code-forge:review --github-pr 123`):

→ **GitHub PR Mode** — Read and follow `skills/review/github-pr-workflow.md`. Do NOT continue with the steps below.

#### 1.0b `--feedback` Flag Provided

If the user passed `--feedback` (e.g., `/code-forge:review --feedback` or `/code-forge:review --feedback #123`):

→ **Feedback Mode** — Read and follow `skills/review/feedback-workflow.md`. Do NOT continue with the steps below.

#### 1.1 Feature Name Provided

If the user provided a feature name (e.g., `/code-forge:review user-auth`):

→ **Feature Mode** — go to Step 2F

#### 1.2 `--project` Flag Provided

If the user passed `--project` (e.g., `/code-forge:review --project`):

→ **Project Mode** with `scope = "full"` — go to Step 2P

#### 1.3 No Arguments

If no arguments provided:

1. Scan **both** `{output_dir}/*/state.json` and `.code-forge/tmp/*/state.json` for all features
2. Filter to features with at least one `"completed"` task
3. Build choice list:
   - If completed features exist: include each as an option, **plus** "Review entire project" as the last option
   - If no completed features: go to **Project Mode** with `scope = "changes"` automatically
4. If only one option (project review): go to **Project Mode** with `scope = "changes"` automatically
5. If multiple options: use `AskUserQuestion` to let user select
   - If user selects "Review entire project": go to **Project Mode** with `scope = "changes"`

---

### Step 2F: Feature Mode — Locate Feature

#### 2F.1 Find Feature

1. Look for `{output_dir}/{feature_name}/state.json`
2. If not found, also check `.code-forge/tmp/{feature_name}/state.json`
3. If still not found: show error, list available features

#### 2F.2 Load Feature Context

1. Read `state.json`
2. Read `plan.md` (for acceptance criteria and architecture)
3. Note completed task count and overall progress

→ Go to Step 3F

---

### Step 2P: Project Mode — Locate Reference

Determine the reference level using a fallback chain.

#### 2P.1 Check for Planning Documents (Level 1: Planning-backed)

Scan `{output_dir}/*/plan.md`:

- If one or more `plan.md` files found → **planning-backed**
- Read all `plan.md` files and aggregate:
  - Acceptance criteria from each feature
  - Architecture decisions
  - Technology stack
- Read corresponding `state.json` files for progress context
- Record: `reference_level = "planning"`
- Record: list of plan file paths and aggregated criteria
- → Go to Step 3P

#### 2P.2 Check for Documentation (Level 2: Docs-backed)

If no planning documents found, scan for upstream documentation:

Search paths (in order):
1. `{input_dir}/*.md` — feature specs
2. `docs/` directory — PRD, SRS, tech-design, test-cases files

Look for files matching patterns:
- `**/prd.md`, `**/srs.md`, `**/tech-design.md`, `**/test-cases.md`
- `**/features/*.md`
- Any `.md` files directly under `docs/`

If documentation files found → **docs-backed**:
- Read all found docs
- Extract: requirements, architecture decisions, acceptance criteria, scope definitions
- Record: `reference_level = "docs"`
- Record: list of doc file paths and extracted criteria
- → Go to Step 3P

#### 2P.3 No Reference (Level 3: Bare)

If neither planning nor docs found → **bare**:
- Record: `reference_level = "bare"`
- → Go to Step 3P

---

### Step 3F: Feature Mode — Collect Changes and Review

#### 3F.1 Collect Change Scope

**From Commits:**
Extract all commit hashes from `state.json` → `tasks[].commits`:
- Flatten all commit arrays into a single list
- If commits are recorded, use `git diff` between the earliest and latest commits
- If no commits recorded, fall back to scanning files involved in tasks

**From Task Files:**
Read all `tasks/*.md` files and collect their "Files Involved" sections:
- Build a complete list of files created/modified by this feature
- Read current state of each file

**Summary:**
- Total files changed
- Total lines added/removed (from git diff)
- List of all affected files

#### 3F.2 Detect Project Type

Before launching the sub-agent, detect the project type to guide dimension selection:

1. **Has frontend?** Check for: `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, HTML templates, CSS/SCSS files, or frontend framework config (`next.config.*`, `vite.config.*`, `angular.json`)
2. **Has backend/service?** Check for: server entry points, API route definitions, database models, middleware
3. **Language ecosystem:** Detect primary language(s) from file extensions and package manifests

Record: `project_type` = `"frontend"` | `"backend"` | `"fullstack"` | `"library"` | `"cli"` | `"unknown"`

#### 3F.3 Multi-Dimension Review (via Sub-agent)

**Offload to sub-agent** to handle the full diff analysis.

Spawn an `Agent` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Review feature: {feature_name}"`

**Sub-agent prompt must include:**
- Feature name and `plan.md` file path
- List of all affected files (sub-agent reads them)
- The acceptance criteria from `plan.md`
- Detected project type
- **MANDATORY pre-analysis instruction:** *"Before applying any review dimension, read every affected file in full and build a call graph for every public method / exported function / entry point in those files. Enumerate — for each — the helpers it calls (to leaves within the reviewed scope), the validations it performs, the state mutations it executes, the errors it raises, and its external-input paths (iteration over arguments, subscript into external data, deserialization). Output this as the `METHOD_CHAINS` section per `references/sub-agent-format.md`. Only after producing METHOD_CHAINS may you apply dimensions. Do not trust method names, plan claims, or helper-function purity — open and read every callee. See the §Call-Graph Discipline section of the parent SKILL.md for the full protocol and anti-rationalization guard."*
- Instructions to review across all applicable dimensions below
- The severity level definitions (blocker / critical / warning / suggestion)
- Instruction: **"For each issue, specify severity, file path, line number/range, what's wrong, and how to fix it. Use the Review Comment Formula: Problem → Why it matters → Suggested fix. When the issue was discovered via the call graph (e.g., a missing validation call, a skipped state mutation, an unguarded external input), reference the relevant METHOD_CHAINS entry in the description."**

**Review dimensions to apply:** Follow [Dimension Application Rules](#dimension-application-rules). **Apply dimensions AGAINST the call graph, not against the surface method body.** A method whose body reads cleanly but whose chain omits expected work is a D1 finding, not a pass.

Additionally, always check **Plan Consistency** (feature mode specific):
- All acceptance criteria from `plan.md` are met
- Architecture matches the design in `plan.md`
- No unplanned features added (scope creep)
- All planned tasks are implemented

**Sub-agent must return the structured format defined in `references/sub-agent-format.md`** (use the Feature Mode `PLAN_CONSISTENCY` consistency section).

→ Go to Step 4F

---

### Step 3P: Project Mode — Collect Source Code and Review

**The primary subject of review is the source code itself.** Reference documents (plans, specs) serve only as criteria to check against — the sub-agent must deeply read and analyze the actual implementation.

#### 3P.1 Collect Source Code

Identify and collect project source files for deep code review. The collection strategy depends on `scope` (set in Step 1):

**If `scope = "changes"` (default — no arguments or auto-selected):**

1. **Identify changed files (primary scope):**
   - If on a non-main branch: `git diff main...HEAD --name-only`
   - If on main branch with uncommitted changes: `git diff HEAD --name-only` + `git diff --cached --name-only` (staged + unstaged)
   - If on main branch with no uncommitted changes: `git diff HEAD~1 --name-only` (last commit)
   - Exclude non-source directories: `node_modules/`, `dist/`, `build/`, `.git/`, `vendor/`, `__pycache__/`, the output directory itself

2. **Expand to impact zone (1 level):** For each changed file, also include:
   - Files that **import or depend on** the changed file (direct dependents — use `Grep` to find import/require/use statements referencing the changed file)
   - Files that the changed file **imports from** (direct dependencies — read the changed file's import statements)
   - **Test files** corresponding to the changed files (e.g., `foo.test.ts` for `foo.ts`)

3. **Fallback to full scan:** Only if no changed files are found (clean repo, no recent commits), fall through to the `scope = "full"` strategy below.

**If `scope = "full"` (`--project` flag):**

1. Use project root markers to find source directories (e.g., `src/`, `lib/`, `app/`, `pkg/`, or language-specific patterns)
2. Exclude non-source directories: `node_modules/`, `dist/`, `build/`, `.git/`, `vendor/`, `__pycache__/`, the output directory itself
3. Scan all source files
4. If the project is large (>50 source files), prioritize:
   - Core modules (entry points, main logic, business logic)
   - Test files
   - Configuration and infrastructure files

**Both modes also collect:**
- Package manifests (`package.json`, `Cargo.toml`, `pyproject.toml`, etc.) for dependency review
- Build/CI configuration if present

#### 3P.2 Detect Project Type

Same as Step 3F.2 — detect `project_type` to guide dimension selection.

#### 3P.3 Multi-Dimension Code Review (via Sub-agent)

**Offload to sub-agent** to handle deep source code analysis.

Spawn an `Agent` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Project code review: {project_name}"`

**Sub-agent prompt must include:**
- Project name and root path
- **List of all source files to review — sub-agent MUST read and analyze each file's actual implementation**
- Reference level (`planning` / `docs` / `bare`) and associated criteria (if any)
- Detected project type
- If planning-backed: aggregated acceptance criteria (as checklist for consistency dimension only)
- If docs-backed: extracted requirements (as checklist for consistency dimension only)
- The severity level definitions (blocker / critical / warning / suggestion)
- Explicit instruction: **"Read every source file. Review the code itself — its logic, structure, correctness, and quality. Reference documents are only used as criteria for the consistency check, not as the subject of review."**
- **MANDATORY pre-analysis instruction:** *"Before applying any review dimension, read every source file in full and build a call graph for every public method / exported function / entry point in those files. Enumerate — for each — the helpers it calls (to leaves within the reviewed scope), the validations it performs, the state mutations it executes, the errors it raises, and its external-input paths (iteration over arguments, subscript into external data, deserialization). Output this as the `METHOD_CHAINS` section per `references/sub-agent-format.md`. Only after producing METHOD_CHAINS may you apply dimensions. Do not trust method names, plan/doc claims, or helper-function purity — open and read every callee. In bare mode (no reference), use the method's name, signature, and public-API promises as the internal consistency check target. See the §Call-Graph Discipline section of the parent SKILL.md for the full protocol and anti-rationalization guard."*
- Instruction: **"For each issue, specify severity, file path, line number/range, what's wrong, and how to fix it. Use the Review Comment Formula: Problem → Why it matters → Suggested fix. When the issue was discovered via the call graph (e.g., a missing validation call, a skipped state mutation, an unguarded external input), reference the relevant METHOD_CHAINS entry in the description."**

**Review dimensions to apply:** Follow [Dimension Application Rules](#dimension-application-rules). **Apply dimensions AGAINST the call graph, not against the surface method body.** A method whose body reads cleanly but whose chain omits expected work is a D1 finding, not a pass.

Additionally, apply the appropriate **Consistency** check based on reference level:

- **planning-backed** → **Plan Consistency:**
  - Aggregated acceptance criteria from all plans are met in the code
  - Implemented architecture matches the designs in plan files
  - No unplanned features added (scope creep)
  - All planned features have corresponding code

- **docs-backed** → **Documentation Consistency:**
  - Code implements the requirements described in documentation
  - Architecture aligns with tech design (if present)
  - Feature scope in code matches what specs describe
  - No undocumented major functionality in the code

- **bare** → **Skip this dimension.** Note in the report: "No reference documents found — consistency check skipped."

**Sub-agent must return the structured format defined in `references/sub-agent-format.md`** (use the Project Mode `CONSISTENCY` consistency section). All issues MUST reference specific source files and line numbers/ranges.

→ Go to Step 4P

---

### Step 4F: Feature Mode — Display Report

Review results are **displayed in the terminal** by default — no file is written. This reflects that reviews are iterative, intermediate checks rather than permanent artifacts.

**Orchestrator validation (before display):** Verify the sub-agent's response contains a non-empty `METHOD_CHAINS` section with at least one entry per public method / exported function in the affected files. If `METHOD_CHAINS` is missing, empty, or lists fewer public symbols than the affected files contain, **reject the response and re-invoke the sub-agent** with an explicit reminder: *"Your previous response was missing METHOD_CHAINS or covered only a subset of public symbols. Re-read every affected file and produce the full call graph per §Call-Graph Discipline before applying dimensions."* Do not display a report built on a skipped pre-analysis — the user would get false confidence. Retry at most twice; after the second failure, surface a visible warning in the report output: `⚠ Sub-agent failed to produce full call-graph — findings may miss chain-level bugs. Consider running /apcore-skills:sync (cross-language projects) or re-running review on a smaller scope.`

Follow the report template in `references/report-template.md` (Feature mode variant).

#### 4F.1 Optional: Save to File (`--save`)

If the user passed `--save` in the arguments, **also** write the report to `{output_dir}/{feature_name}/review.md`. Otherwise, do NOT create the file.

→ Go to Step 5F

---

### Step 4P: Project Mode — Display Report

**Orchestrator validation (before display):** Same rule as Step 4F — verify `METHOD_CHAINS` covers every public method / exported function in the collected source files. Reject + re-invoke if missing or thin. In project mode the file set can be large; the sub-agent MAY split METHOD_CHAINS into groups-by-file, but total coverage must hit every public symbol. If the sub-agent legitimately cannot cover every symbol within a single response (e.g., 500+ public functions), it MUST explicitly list the un-analyzed symbols in a `METHOD_CHAINS_DEFERRED` block with reason `"scope-too-large"` — this surfaces to the user as: `⚠ {N} public symbols not analyzed due to scope — consider narrowing via --project scope=changes or per-feature review`. Never silently skip.

Follow the report template in `references/report-template.md` (Project mode variant).

#### 4P.1 Optional: Save to File (`--save`)

If the user passed `--save` in the arguments, **also** write the report to `{output_dir}/project-review.md`. Otherwise, do NOT create the file.

→ Go to Step 5P

---

### Step 5F: Feature Mode — Update state.json

1. Read `state.json`
2. Add or update `review` field in metadata:
   ```json
   {
     "review": {
       "date": "ISO timestamp",
       "rating": "pass_with_notes",
       "merge_readiness": "fix_required",
       "total_issues": 12,
       "blockers": 0,
       "criticals": 2,
       "warnings": 6,
       "suggestions": 4
     }
   }
   ```
   - If `--save` was used, also include `"report": "review.md"` in the review object
3. Update `state.json` `updated` timestamp

→ Go to Step 6

---

### Step 5P: Project Mode — No State Update

Project mode does not update any `state.json` — there is no single feature state to track.

→ Go to Step 6

---

### Step 6: Summary and Next Steps

**CRITICAL — Next-step commands are MANDATORY.** When the review finds any blocker, critical, or warning issues, you MUST include the `/code-forge:fix --review` command in the summary output. Never omit it, never paraphrase it, never skip the next-steps block.

#### 6.1 Feature Mode

Display:

```
Code Review Complete: {feature_name}

Rating: {overall_rating}
Merge Readiness: {merge_readiness}
Issues: {total_issues} ({blocker_count} blockers, {critical_count} critical, {warning_count} warnings, {suggestion_count} suggestions)
{If --save was used:}
Report saved: {output_dir}/{feature_name}/review.md

{If needs_changes (blockers or criticals > 0):}
🚫 Merge blocked — fix these first:
  1. {highest priority blocker/critical with file:line}
  2. {next priority fix}
  ...
  Fix all:    /code-forge:fix --review
  Re-review:  /code-forge:review {feature_name}

{If pass_with_notes (warnings > 0, no blockers/criticals):}
⚠ Merge OK with notes — consider fixing:
  1. {top warning}
  2. ...
  Fix all:    /code-forge:fix --review

{If pass:}
✅ Ready for next steps:
  /code-forge:status {feature_name}         View final status
  Create a Pull Request

Tip: use --save to persist the review report to disk
```

#### 6.2 Project Mode

Display:

```
Project Review Complete: {project_name}

Rating: {overall_rating}
Merge Readiness: {merge_readiness}
Reference: {planning-backed (N plans) | docs-backed (N documents) | bare}
Issues: {total_issues} ({blocker_count} blockers, {critical_count} critical, {warning_count} warnings, {suggestion_count} suggestions)
{If --save was used:}
Report saved: {output_dir}/project-review.md

{If needs_changes (blockers or criticals > 0):}
🚫 Issues require attention:
  1. {highest priority blocker/critical with file:line}
  2. {next priority fix}
  ...
  Fix all:    /code-forge:fix --review
  Re-review:  /code-forge:review --project

{If pass_with_notes (warnings > 0, no blockers/criticals):}
⚠ Project quality acceptable with notes — consider fixing:
  1. {top warning}
  2. ...
  Fix all:    /code-forge:fix --review

{If pass:}
✅ Project quality looks good.

Tip: use --save to persist the review report to disk
```
