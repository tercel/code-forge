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
Config → Determine Mode → Locate Reference → Collect Scope → Module Grouping (trial)
  → Fast path (< 3 files OR only 1 module group):  Single sub-agent (all 15 dims)
  → Layered path (≥ 3 files AND ≥ 2 module groups):
       • Parallel per-module agents
           · Primary: full review (D1–D4, D6, D8–D9) on their own module files
           · Tier-2:  depth-1 expansion into cross-module callees that are ALSO in the diff
             (closes the blind spot where caller and callee live in different modules but both in scope)
       • Cross-module agent
           · D5, D7, D10–D15 + CROSS_MODULE_CONSISTENCY + SECOND_ORDER_REVIEW
           · Consumes aggregated METHOD_CHAINS (with X:-prefixed tier-2 inlined steps visible)
→ Merge + Deduplicate + Validate → Display Report → Update State → Summary
```

## Context Management

The review analysis is offloaded to sub-agents to handle large diffs without exhausting the main context. For changes spanning multiple modules, parallel per-module agents each hold a bounded, module-scoped context window — while still being able to see one level into cross-module callees that are part of the same diff (tier-2 expansion). This closes the cross-module defensive-gap blind spot without re-introducing the full-diff context dilution that causes "whack-a-mole" defects.

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

**Three-tier expansion rule — the graph must enumerate, for every public method:**

**Tier 1 — Same-module private helpers: FULL recursive inlining.**
When a public method calls a private helper defined in the same reviewed scope (same file, or a nearby private module within the same module group), you MUST open that helper and **inline its steps** (validations, mutations, raises, iterates, subscripts, calls-to-further-helpers) into the public method's chain. Recurse to leaves. Do NOT leave a private same-scope helper as an opaque `call` step — that hides exactly the bugs this discipline exists to catch.

**Tier 2 — Cross-module callees that are ALSO in the review scope: DEPTH-1 expansion.**
When a public method calls a function/method defined in a **different module group BUT still part of the current review scope** (i.e., the callee's file is also in the diff / affected-files list), you MUST open that callee's file, read the called method's body, and **inline its top-level steps at depth 1** (direct validations, mutations, raises, iterates, subscripts, and immediate sub-calls to its own private helpers — but do NOT recurse deeper into the callee's private helpers beyond one level). Mark these inlined steps with the `X:` prefix and the fully-qualified callee name to make the cross-module boundary visible:

```
- { kind: call,      detail: "DisplayResolver.resolve(node)", line: 45 }
- { kind: call,      detail: "  X:DisplayResolver.resolve → for surface in node.surfaces", line: 78 }
- { kind: subscript, detail: "  X:DisplayResolver.resolve → surface['values']  (unguarded)", line: 82 }
- { kind: raise,     detail: "  X:DisplayResolver.resolve → TypeError if surface not dict", line: 85 }
```

Rationale: a cross-module callee that is itself being modified in this diff is part of the same logical change unit as the caller. If `DisplayResolver.resolve` has an unguarded subscript, a caller that invokes it over external input is exposed to that bug. Treating the callee as an opaque `ext_call` re-creates the very blind spot the discipline exists to close.

**Tier 3 — Leaves (NO expansion):**
- Stdlib calls (`json.loads`, `os.path.join`)
- Third-party library calls (`requests.get`, `pydantic.BaseModel.model_validate`)
- Framework calls (`Flask.route`, `React.useState`)
- Private helpers / methods defined in a file that is **NOT in the current review scope** (untouched code outside the diff)

Represent all tier-3 steps as `ext_call` with no further expansion.

---

**The graph must enumerate, for every public method:**
1. **Every step in the execution path** — including tier-1 recursive inlining and tier-2 depth-1 cross-module inlining per the rule above.
2. **Every validation performed anywhere in the chain** (early `if/raise`, `assert`, `match`, type guards, schema validation, Protocol checks, `isinstance`, `instanceof`) — including validations inside all inlined bodies.
3. **Every state mutation anywhere in the chain** (writes to `self.x` / `this.x`, inserts into maps/sets/lists, event emissions, lock acquisitions, external I/O) — including mutations inside all inlined bodies.
4. **Every error raised anywhere in the chain** (`raise`, `throw`, `return Err`, `return nil, err`) — including raises inside all inlined bodies.
5. **Every external input path anywhere in the chain** (iteration over arguments, subscript/indexing into external data — especially data returned by plugin/discoverer/factory callbacks, deserialization of user/plugin/config input, network reads) — including paths inside all inlined bodies. This is where defensive-gap bugs live and they are almost always inside private helpers OR inside cross-module callees.

**Inlining convention.** When inlining a helper's steps into a public method's chain, prefix the `detail` field to preserve the call hierarchy:

- **Tier-1 (same-module):** `  helper_name →` (2-space indent + helper name)
- **Tier-2 (cross-module in diff):** `  X:Module.method →` (2-space indent + `X:` marker + fully-qualified callee)

Example combining both tiers:

```
# Tier-1 same-module helper inlining
- { kind: call,      detail: "_discover_custom(rootPaths)", line: 257 }
- { kind: call,      detail: "  _discover_custom → custom_discoverer.discover(roots)", line: 262 }
- { kind: iterate,   detail: "  _discover_custom → for entry in custom_modules", line: 263 }
- { kind: subscript, detail: "  _discover_custom → entry['module_id']  (unguarded, KeyError crashes loop)", line: 269 }

# Tier-2 cross-module callee (in diff) — depth-1 inlining
- { kind: call,      detail: "self._resolver.resolve(module)", line: 272 }
- { kind: call,      detail: "  X:DisplayResolver.resolve → for surface in module.surfaces", line: 78 }
- { kind: subscript, detail: "  X:DisplayResolver.resolve → surface['values']  (unguarded)", line: 82 }
- { kind: ext_call,  detail: "  X:DisplayResolver.resolve → self._apply_coerce(surface)  [tier-3: private helper not recursed]", line: 85 }
```

The indentation + prefix preserves the call hierarchy without needing a separate nested-list structure. The `X:` marker tells the reviewer "this step lives in a different module than the chain's root method but is still within the review scope" — which is exactly the signal the cross-module association pass needs.

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
| "The method calls into another module — that's cross-module, so it's an `ext_call` leaf" | Only true if the callee is NOT in the current review scope. If the callee's file is **also being modified in this diff**, it is part of the same logical change unit and must be expanded at tier-2 (depth-1) with the `X:` marker. Treating an in-diff cross-module callee as opaque produces exactly the failure mode the layered-review architecture exists to prevent: defensive gaps that straddle module boundaries become invisible to both the per-module agent (didn't open the callee) and the cross-module agent (received only chain summaries, can't re-derive the gap). If `CallerModule.foo()` calls `CalleeModule.bar()` and both files are in the diff, the per-module agent handling `CallerModule` MUST open `CalleeModule.bar` and inline its top-level body. |

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

#### 3F.3 Module Grouping

Determine which review path to use based on the scope shape:

1. **Trial grouping:** Apply the grouping rules below to the affected files set.
2. **Decision:**
   - **Fast path (3F.4a):** fewer than 3 affected files, OR grouping yields only 1 module group (all files in the same module — no cross-module axis to analyze)
   - **Layered path (3F.4b → 3F.5):** grouping yields ≥ 2 module groups AND total affected files ≥ 3

Rationale: the layered path only pays off when there is actual cross-module territory to cover. A 5-file change all inside `src/binding/` has no cross-module axis and should stay in the fast path.

**Module grouping rules:**
1. Group files by directory/package (files in the same directory = one group). For Python projects, group by top-level package; for TypeScript, group by `src/` subdirectory.
2. Identify **cross-cutting files** (shared utilities, base classes, `__init__.py`, `index.ts`, `exports.ts`, `types.ts`) — mark them as `cross_cutting: true`. Include them in BOTH their module group AND the cross-module agent's file list.
3. Cap each group at 4 files — if a group exceeds 4, split by file role (models / serializers / logic / tests).
4. Record: `module_groups = [{group_id, files[], cross_cutting_files[]}]`
5. Record the complete `in_diff_files` list (every affected file across all groups, including cross-cutting). Each per-module agent will receive this list alongside its own `primary_files`; the agent applies the three-tier rule at chain-building time — if a call target's file is in `in_diff_files` but not in its `primary_files`, that callee is tier-2. No static import pre-analysis is needed (and would be unreliable anyway given barrel re-exports, aliased imports, and dynamic imports).

---

#### 3F.4a Fast Path: Single Sub-agent Review (< 3 files, OR only 1 module group)

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
- Instructions to review across all applicable dimensions
- The severity level definitions (blocker / critical / warning / suggestion)
- Instruction: **"For each issue, specify severity, file path, line number/range, what's wrong, and how to fix it. Use the Review Comment Formula: Problem → Why it matters → Suggested fix. When the issue was discovered via the call graph (e.g., a missing validation call, a skipped state mutation, an unguarded external input), reference the relevant METHOD_CHAINS entry in the description."**

**Review dimensions to apply:** Follow [Dimension Application Rules](#dimension-application-rules). **Apply dimensions AGAINST the call graph, not against the surface method body.**

Additionally, always check **Plan Consistency** (feature mode specific):
- All acceptance criteria from `plan.md` are met
- Architecture matches the design in `plan.md`
- No unplanned features added (scope creep)
- All planned tasks are implemented

**Sub-agent must return the structured format defined in `references/sub-agent-format.md`** (use the Feature Mode `PLAN_CONSISTENCY` consistency section).

→ Go to Step 4F

---

#### 3F.4b Parallel Per-Module Review (≥ 3 files AND ≥ 2 module groups)

Spawn **one sub-agent per module group in a single parallel message** (all `Agent` calls sent together).

For each module group, spawn `Agent` with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Per-module review: {feature_name}/{group_id}"`

**Sub-agent prompt must include:**
- **`primary_files`** — this module group's own files (the sub-agent reads these in full and produces top-level METHOD_CHAINS entries for their public symbols)
- **`in_diff_files`** — the complete list of every affected file across ALL module groups in this review. This is the tier-2 eligibility set — when a call's target definition lives in `in_diff_files \ primary_files`, the agent MUST open that file and inline its top-level body at depth-1 with the `X:` prefix.
- Feature name and plan.md acceptance criteria (for context — not a consistency check)
- Detected project type
- **MANDATORY pre-analysis:** the three-tier expansion rule from §Call-Graph Discipline:
  - **Tier 1 (same-module private helpers — file in `primary_files`):** full recursive inlining
  - **Tier 2 (cross-module callees — file in `in_diff_files` but NOT in `primary_files`):** depth-1 expansion with `X:Module.method →` prefix
  - **Tier 3 (everything else — stdlib, third-party, or files in neither list):** `ext_call` leaf, no expansion
- **Intra-module dimensions to apply:** D1 (Functional Correctness), D2 (Security), D3 (Resource Management), D4 (Code Quality), D6 (Performance), D8 (Error Handling), D9 (Observability) — applied against the chain INCLUDING tier-2 inlined steps (a D1 defensive gap inside a tier-2 callee IS reported by this agent)
- **Do NOT apply:** D5, D7, D10-D15 — these are handled in the cross-module pass
- The severity level definitions (blocker / critical / warning / suggestion)
- Return format: **Per-Module sub-agent format** (see `references/sub-agent-format.md` §Per-Module format). The output must include `primary_files` (same as input), `tier2_files` (the subset of `in_diff_files` actually opened for tier-2 expansion), and `METHOD_CHAINS` with top-level entries only for public symbols in `primary_files`.
- Instruction: *"Return ALL issues found in chains rooted at YOUR module's public symbols — including issues discovered via tier-2 inlined steps from cross-module callees. When a finding lives in a tier-2 inlined step, set the issue's `file` to the tier-2 callee's file (not your module's file). Do not self-filter or defer cross-module concerns — the cross-module agent handles CONSISTENCY across modules, but defensive gaps visible in your chain are yours to flag even if they live in someone else's file."*

**Deduplication note:** When agent A (owning module X) tier-2-expands into `ModuleY.foo` and flags a defensive gap, agent B (owning module Y) will independently tier-1-inline `foo` as part of its full review and likely flag the same gap. The orchestrator MUST deduplicate in Step 4F (merge step) by `(file, line, title)`.

**Wait for all per-module sub-agents to complete before proceeding to 3F.5.**

---

#### 3F.5 Cross-Module Association Review

After all per-module agents complete, spawn **one cross-module aggregation sub-agent**.

`Agent` with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Cross-module review: {feature_name}"`

**Sub-agent prompt must include:**
- All per-module `METHOD_CHAINS` outputs verbatim (copy from 3F.4b results)
- All per-module findings (to avoid duplicate flagging — cross-module agent adds NEW findings only)
- Cross-cutting files list + the sub-agent reads their full content
- plan.md content and acceptance criteria
- List of all affected files grouped by module (structural map of the feature)
- Detected project type
- The severity level definitions (blocker / critical / warning / suggestion)

**Dimensions to apply (cross-module scope):**
- **D5** (Architecture & Design) — layer boundary violations, circular deps, coupling across the full module set
- **D7** (Test Coverage) — coverage gaps across the full feature scope, test files for each module
- **D10–D13** (Standards, Backward Compat, Maintainability, Dependencies)
- **D15** (Simplification & Anti-Bloat) — cross-module duplicate detection requires the full picture; per-module agents cannot catch parallel implementations across file boundaries

**CROSS_MODULE_CONSISTENCY — apply all five checks:**

1. **Coerce/guard pattern:** If module A guards `entry.get("key", default)` on dict external inputs, do all sibling modules with structurally equivalent dict-subscript external inputs follow the same pattern? Flag inconsistency as `critical`.
2. **Traceback preservation:** If module A uses `raise X from e` or passes `exc_info=True` in exception logging, are all modules in the diff consistent? Flag inconsistency as `warning`.
3. **Re-export completeness:** For every new public symbol introduced in a submodule, verify it appears in the package `__init__.py` / `index.ts` / `__all__` if the project re-exports its API surface. Flag missing re-exports as `warning`.
4. **Error handling convention:** Same error base class hierarchy and chaining approach used across all modules? Flag deviation as `warning`.
5. **Defensive coding depth:** If module A added input validation guards for a specific data path, are all modules with structurally equivalent data paths at the same validation depth? Flag depth mismatch as `critical`.

**SECOND_ORDER_REVIEW — active prevention of D-series ("whack-a-mole") bugs:**

For each fix pattern visible in the diff (identifiable from per-module METHOD_CHAINS + intra-module findings):
1. Extract the fix pattern (e.g., "coerce non-dict display surface values", "snapshot sys.path before exec_module", "preserve traceback on scan failure", "emit `suggested_alias` in serializer output")
2. Identify all code paths in OTHER modules in the diff that handle structurally similar data flows
3. Verify the same fix has been applied to each structurally similar path
4. If the fix is missing in any sibling module, emit a `critical` finding: *"Fix pattern applied in {module_A} was not propagated to {module_B} — structural parity violation. Pattern: {description}. Expected location: {file:line estimate}."*

**Plan Consistency** (always, feature mode):
- All acceptance criteria from `plan.md` are met across the full combined module set
- Architecture matches the design in `plan.md`
- No unplanned features added across any module
- All planned tasks are implemented

**Return format:** Cross-Module sub-agent format (see `references/sub-agent-format.md` §Cross-Module format)

→ Proceed to Step 4F with merged results from 3F.4b + 3F.5

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

#### 3P.3 Module Grouping (Project Mode)

Apply the same module grouping logic as Step 3F.3 (trial grouping + 2-axis trigger):

- **Fast path (3P.3a):** fewer than 3 source files in scope, OR grouping yields only 1 module group
- **Layered path (3P.3b → 3P.4):** grouping yields ≥ 2 module groups AND total source files ≥ 3

**Module grouping rules:** same as 3F.3 — by directory/package, max 4 files/group, identify cross-cutting files, and record `in_diff_files` (passed to every per-module agent as the tier-2 eligibility set).

---

#### 3P.3a Fast Path: Single Sub-agent Review (< 3 files, OR only 1 module group)

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
- **MANDATORY pre-analysis instruction:** *"Before applying any review dimension, read every source file in full and build a call graph for every public method / exported function / entry point in those files. Enumerate — for each — the helpers it calls (to leaves within the reviewed scope), the validations it performs, the state mutations it executes, the errors it raises, and its external-input paths. Output this as the `METHOD_CHAINS` section per `references/sub-agent-format.md`. Only after producing METHOD_CHAINS may you apply dimensions. In bare mode, use the method's name, signature, and public-API promises as the internal consistency check target. See the §Call-Graph Discipline section of the parent SKILL.md for the full protocol."*
- Instruction: **"For each issue, specify severity, file path, line number/range, what's wrong, and how to fix it. Use the Review Comment Formula: Problem → Why it matters → Suggested fix."**

**Review dimensions:** All applicable dimensions. Apply against the call graph, not surface method bodies.

Apply the appropriate **Consistency** check based on reference level:
- **planning-backed** → Plan Consistency (criteria met, no scope creep, architecture match)
- **docs-backed** → Documentation Consistency (requirements implemented, architecture aligned)
- **bare** → Skip. Note in report: "No reference documents found — consistency check skipped."

**Sub-agent must return the structured format defined in `references/sub-agent-format.md`** (Project Mode `CONSISTENCY` section). All issues MUST reference specific source files and line numbers/ranges.

→ Go to Step 4P

---

#### 3P.3b Parallel Per-Module Review (≥ 3 files AND ≥ 2 module groups)

Same protocol as 3F.4b — spawn one sub-agent per module group in parallel. Each agent receives:

- **`primary_files`** — its module group's own files (reviewed in full, top-level METHOD_CHAINS entries for their public symbols)
- **`in_diff_files`** — the complete affected-files list; any call target whose file is in `in_diff_files \ primary_files` must be tier-2-expanded per §Call-Graph Discipline
- Three-tier expansion pre-analysis instruction (same as 3F.4b)
- Applies D1, D2, D3, D4, D6, D8, D9 against chains INCLUDING tier-2 inlined steps
- Returns Per-Module sub-agent format (see `references/sub-agent-format.md` §Per-Module format)

Wait for all per-module sub-agents to complete before proceeding.

#### 3P.4 Cross-Module Association Review (Project Mode)

Same protocol as 3F.5, with the following adjustments:

- Instead of Plan Consistency, apply the appropriate **Consistency** check based on `reference_level`:
  - **planning-backed** → Plan Consistency across the full aggregated method chain set
  - **docs-backed** → Documentation Consistency
  - **bare** → Skip consistency; still apply all five CROSS_MODULE_CONSISTENCY checks and SECOND_ORDER_REVIEW
- All five CROSS_MODULE_CONSISTENCY checks (coerce/guard, traceback, re-export, error convention, defensive depth)
- SECOND_ORDER_REVIEW (same as 3F.5)
- D5, D7, D10–D15

Return format: Cross-Module sub-agent format (see `references/sub-agent-format.md` §Cross-Module format)

→ Go to Step 4P with merged results from 3P.3b + 3P.4

---

### Step 4F: Feature Mode — Display Report

Review results are **displayed in the terminal** by default — no file is written. This reflects that reviews are iterative, intermediate checks rather than permanent artifacts.

**Orchestrator validation (before display):**

*Fast path (3F.4a):* Verify the single sub-agent's response contains a non-empty `METHOD_CHAINS` section with at least one entry per public method / exported function in the affected files. If `METHOD_CHAINS` is missing, empty, or lists fewer public symbols than the affected files contain, **reject and re-invoke** with an explicit reminder: *"Your previous response was missing METHOD_CHAINS or covered only a subset of public symbols. Re-read every affected file and produce the full call graph per §Call-Graph Discipline before applying dimensions."* Retry at most twice; after the second failure, surface: `⚠ Sub-agent failed to produce full call-graph — findings may miss chain-level bugs. Consider re-running review on a smaller scope.`

*Layered path (3F.4b + 3F.5):*
1. For each per-module agent result, verify `METHOD_CHAINS` covers all public symbols in that module group's files. Reject and re-invoke any module agent that returned empty or under-covered METHOD_CHAINS (same retry/warning logic as fast path, but scoped per module).
2. Verify the cross-module agent result contains `CROSS_MODULE_CONSISTENCY` and `SECOND_ORDER_REVIEW` sections. If either is missing, reject and re-invoke the cross-module agent once.
3. **Merge all findings:** Collect issues from all per-module agents + the cross-module agent. Deduplicate by `(file, line, title)` — if the same finding appears in both a module agent and the cross-module agent, keep the cross-module version (it has more context).
4. Construct a single unified `REVIEW_SUMMARY` with aggregate counts across all agents.
5. Append a **Cross-Module section** to the report (see `references/report-template.md` §Cross-Module section).

Follow the report template in `references/report-template.md` (Feature mode variant).

#### 4F.1 Optional: Save to File (`--save`)

If the user passed `--save` in the arguments, **also** write the report to `{output_dir}/{feature_name}/review.md`. Otherwise, do NOT create the file.

→ Go to Step 5F

---

### Step 4P: Project Mode — Display Report

**Orchestrator validation (before display):**

*Fast path (3P.3a):* Verify `METHOD_CHAINS` covers every public method / exported function in the collected source files. Reject + re-invoke if missing or thin. In project mode the file set can be large; the sub-agent MAY split METHOD_CHAINS into groups-by-file, but total coverage must hit every public symbol. If the sub-agent legitimately cannot cover every symbol within a single response (e.g., 500+ public functions), it MUST explicitly list the un-analyzed symbols in a `METHOD_CHAINS_DEFERRED` block with reason `"scope-too-large"` — this surfaces to the user as: `⚠ {N} public symbols not analyzed due to scope — consider narrowing via --project scope=changes or per-feature review`. Never silently skip.

*Layered path (3P.3b + 3P.4):* Apply the same merge and validation logic as Step 4F layered path — verify per-module METHOD_CHAINS coverage, verify cross-module agent produced CROSS_MODULE_CONSISTENCY and SECOND_ORDER_REVIEW sections, merge all findings, deduplicate by `(file, line, title)`, construct unified REVIEW_SUMMARY. Append a **Cross-Module section** to the report.

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
