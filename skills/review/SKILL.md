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

All issues use a 4-tier severity system, ordered by merge-blocking priority. **Severity is assigned strictly per the definitions below and re-verified by §Finding Suppression Gate Gate 3 before the finding is emitted.**

| Severity     | Symbol | Meaning                                                                                                                                                                                                                              | Merge Policy              |
|--------------|--------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------|
| `blocker`    | :no_entry: | Production data loss, security breach with a real attacker model, or crash on normal-use inputs. Reproducible on day one. **Requires `evidence` field.**                                                                             | **Must fix before merge** |
| `critical`   | :warning: | Demonstrable correctness bug with a concrete reachable trigger in the project's actual use case, producing observable wrong behavior. **NOT:** design preferences, pattern inconsistencies, speculative edge cases. **Requires `evidence` field.** | **Must fix before merge** |
| `warning`    | :large_orange_diamond: | Fix recommended **with a concrete, named downside** — cross-module inconsistency that produces divergent caller behavior, missing guard on a GENUINELY external input (Gate 2), missing test on a path with an observable failure mode, silent divergence from a convention the project enforces for a behavioral reason. **NOT** pure pattern or stylistic divergence. If you cannot name the observable downside in one line, the finding is noise — drop. `evidence` SHOULD be provided; when omitted, the description itself must name the downside. **Additional rule — factual claims (Gate 5):** if the description asserts a falsifiable property of the codebase ("zero references", "never called", "dead code", "only used in X", "duplicates Y", "N lines exceed limit"), the finding MUST carry a verification artifact in `evidence` (the actual grep/search command AND a representative slice of its output, OR explicit file:line citations proving the claim). Unverified factual claims are dropped by Gate 5 — not downgraded. | Should fix                |
| `suggestion` | :blue_book: | Concrete improvement with an observable benefit — dead code deletion, comment clarifying a non-obvious invariant, extraction of a duplicated block that has drifted. **NOT** "defensive improvements for unlikely scenarios", **NOT** speculative "might be clearer / nicer / simpler" preferences, **NOT** pure renames for clarity, **NOT** "consider using X instead of Y" style swaps, **NOT** extract-helper proposals against <3 lines of near-duplication, **NOT** formatting / casing consistency (linter territory). If the benefit cannot be named concretely AND the current code is functional, drop. Also subject to the **suggestion budget** and **same-theme consolidation** rules enforced at orchestrator validation time — see Step 4F validation #6. `evidence` optional; when the suggestion makes a factual claim (see Gate 5), verification is still required. | Nice-to-have              |

**Speculative-phrasing drop rule.** If a finding's description relies on speculative phrasing ("could theoretically", "if X ever happens", "in case someone", "potentially might", "might be nicer", "smells wrong", "feels off"), **DROP the finding at ANY severity**. Previously this was "downgrade one level", but downgrading merely relocated noise into `warning`/`suggestion` where no further gate ran; the only action that actually cleans the report is to drop. The rescue path is to rewrite the description with a concrete, reachable trigger and re-submit. Full protocol in §Finding Suppression Gate Gate 3.

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

## Finding Suppression Gate (Mandatory Pre-Emission Check)

**Before the sub-agent writes ANY finding into the output YAML, it MUST pass that finding through the four gates below.** A finding that fails a gate is either DROPPED or DOWNGRADED per the gate's instructions. This discipline is required because the dimensional framework in `references/dimensions.md` pushes the agent toward exhaustive per-dimension checking — without counter-pressure, that bias produces speculative noise: "if metadata ever holds non-primitives", "could theoretically RecursionError on self-referential dicts", "attacker-controlled `module_id` in a dev tool reading the user's own local files". Such findings waste reviewer attention, inflate counts, and erode trust in the report.

The gates are applied **after** call-graph analysis and dimension classification, **before** the issue is serialized into the YAML output. Every finding in the final report is an output of this gate.

### Gate 1 — Reachability

**Question:** Under the project's actual use case — the one the README / project type / threat model describes — is the failure mode reachable by a concrete input the user could hit?

**Drop the finding if any of these is true:**
- The trigger requires inputs that the project's use case excludes (e.g., "self-referential dict causes RecursionError" in a YAML config written by humans — humans don't author self-referential YAML).
- The trigger requires bugs in upstream code that the type system or upstream invariant already prevents.
- The description starts with or leans on: **"if X ever happens"**, **"could theoretically"**, **"in case someone passes"**, **"potentially might"**, **"non-deterministic in unspecified scenario"**. These phrases are speculative tells — the finding has no concrete reproduction path.
- The "failure" requires the developer to author malicious input against their own tool (e.g., "a malicious scanner could emit `\"\"\"` in the module_id" — the developer writing their own scanner is not a threat actor).

**Keep the finding** only when there is a concrete, demonstrable input reachable in the project's actual use case. Record the trigger in the issue's `evidence` field.

### Gate 2 — Trust Boundary (applies to D1 defensive-gap and all D2 security findings)

**Question:** Does the input source actually cross a trust boundary the project's threat model recognizes?

**External sources (real trust boundary) — D1/D2 findings here are valid:**
- Network requests / HTTP / WebSocket / RPC payloads from untrusted peers
- Untrusted user input (form fields, query params, uploaded files)
- Third-party API responses
- Cross-tenant / cross-user data in a multi-tenant system
- Public package / plugin registries consumed by published software
- Files uploaded or fetched from outside the project's own repo

**Internal sources (NO trust boundary) — D1/D2 findings here are noise; DROP unless the project declares a stricter threat model in its README / SECURITY.md:**
- The project's own source files being scanned by the project's own tooling (dev tools, code generators, linters, build scripts)
- Hard-coded constants committed to the repo
- Config files committed to the repo that the developer themselves authored
- Function arguments inside a single trusted process with type-checked signatures
- Data produced by the project's own build pipeline upstream of the point in question

**Canonical anti-pattern to drop:** *"`module_id` could contain `\"\"\"` and inject code into the generated docstring if a malicious scanner / malicious YAML / malicious developer produces it."* The developer running their own dev tool against their own code is not in the threat model. Drop.

**Keep the finding** when the input genuinely crosses a recognized trust boundary, OR the project is itself security-sensitive (auth, crypto, payment processing, multi-tenant SaaS, anything handling secrets of parties other than the developer). **When in doubt for a clearly internal developer tool, drop.**

### Gate 3 — Severity Calibration

Re-check the severity you assigned after writing the description. Each level has a STRICT meaning:

- **`blocker`** — Production data loss, security breach with a real attacker model, or crash on normal-use inputs. Reproducible failure mode the user hits on day one.
- **`critical`** — Demonstrable correctness bug with a concrete, reachable trigger in the project's actual use case, affecting observable behavior. **NOT:** design preferences, "inconsistent with sibling code", speculative edge cases, or defensive-improvement suggestions.
- **`warning`** — Fix recommended with a concrete, reproducible downside. Cross-module inconsistency that causes divergent caller behavior, missing guard on a GENUINELY external input (Gate 2), missing test on a path with an observable failure mode, silent divergence from a convention the project enforces with a behavioral reason. **NOT** pure pattern/style divergence — if you cannot name the observable downside, the finding is noise. Drop it.
- **`suggestion`** — Concrete improvement with an observable benefit (dead code deletion, comment clarifying a non-obvious invariant, extraction of a duplicated drifted block). **NOT** "defensive improvements for unlikely scenarios", **NOT** speculative "might be nicer to" preferences. If the benefit cannot be named concretely and the code is functional as-is, drop.

**Downgrade rules — apply these mechanically:**

1. If the description contains any of the speculative phrases from Gate 1, **DROP the finding entirely — do not downgrade-and-keep**. Speculative phrasing is a Gate 1 failure at ANY severity (critical, warning, OR suggestion). Downgrading preserves the noise in the report; dropping is the correct action. The only rescue path: rewrite the description citing a concrete, reachable trigger. If you cannot, drop.
2. If the finding describes a **design choice** (fail-fast vs collect-errors, sync vs async, strict vs permissive) without pointing to a concrete observable failure in the chosen design, **max severity is `warning`**. "Inconsistent with sibling writer" is a warning-level consistency note, not a critical.
3. If the finding is "code doesn't validate an input", check Gate 2 first. If the input source is internal/trusted and type-checked, **drop**. If external, **critical** is warranted only when a malformed input produces a concrete wrong behavior (not just "raises an unexpected exception type").
4. If the finding's fix is "add a guard / add a log / add a doc comment / rename for clarity" with no observable bug behind it, **max severity is `suggestion`**.

### Gate 4 — Quota Avoidance

**The dimension list does NOT impose a finding quota. Empty dimensions are a VALID and CORRECT result.**

If you finish analyzing D8 / D11 / D13 / etc. and have zero real findings, write `issues: []` for that dimension and move on. **DO NOT produce a marginal finding to "show you reviewed the dimension"** — the orchestrator never penalizes empty dimensions; it rejects fabricated ones.

Symptoms that you are quota-filling (stop and drop the finding):
- You are writing a finding whose severity you had to argue yourself into.
- The finding's `why it matters` requires a three-step hypothetical chain ("if A and then B and then C").
- You reached for the finding because the dimension felt under-utilized, not because you found a problem.

The one exception is **D15 (Simplification & Anti-Bloat)** where empty findings are still valid but the agent must *demonstrate* it grep'd for duplicates and read import graphs — see D15's execution requirements in `dimensions.md`.

### Gate 5 — Factual Verifiability (applies to ANY finding that asserts a codebase property)

**Question:** Does this finding's description or evidence make a falsifiable claim about the codebase — and if so, does `evidence` include the verification artifact that would prove the claim?

This gate exists because the dimensional framework rewards specific-sounding assertions ("zero references", "duplicated in three places", "dead code") — but nothing in the Gate 1–4 pipeline *verifies* those assertions are true. A sub-agent writing *"grep returns only the declaration; zero reads"* can ship the finding green when the symbol is actually read three times elsewhere. This is the most common pattern of factually-wrong warnings and the prior gates cannot catch it.

**Trigger phrases — the finding MUST carry a verification artifact when the description OR evidence contains any of these:**
- `"zero references"`, `"zero reads"`, `"never called"`, `"never read"`, `"never invoked"`, `"no callers"`
- `"dead code"`, `"unreachable"`, `"no-op in practice"`, `"unused"`
- `"only used in"`, `"only referenced in"`, `"only read at"`, `"sole consumer"`
- `"duplicates X"`, `"copy of X"`, `"redeclares"`, `"parallel implementation"`, `"reimplements"`
- `"N lines"` where N is a specific count, `"exceeds (50|N) lines"`, `"LOC"` with a specific number
- `"grep returns"`, `"grep shows"`, `"search finds"` — any claim about search results

**Required verification artifact — `evidence` must include at least ONE of:**
1. The **actual search command** executed (e.g., `grep -rn "ERROR_CODE_MAP" src/`) **AND** a representative slice of its output (matched lines with file:line, OR `"0 matches"` if claiming absence). Single-line summaries like *"grep returns only the declaration"* without the actual matched-line output are insufficient — the verification artifact must be the output itself, not a paraphrase.
2. **Explicit file:line citations** listing every site the claim covers (e.g., for a "duplicates X" claim, cite both the original and the duplicate; for "only used in foo.ts", cite the original definition AND every use site).
3. For `"N lines"` / LOC claims: the file:line range being measured and how the count was derived (e.g., `"main.ts:801-1154 = 354 lines"` — a range that can be checked).

**Drop the finding if:**
- The trigger phrase appears but `evidence` has no command+output and no file:line citations supporting the claim. The sub-agent is asserting without showing.
- The trigger phrase is "only used in X" / "only referenced in X" but evidence cites only the definition site — the claim is about absence of OTHER uses; evidence must demonstrate the negative (the grep output showing no other matches).
- The trigger phrase is "duplicates X" but evidence shows only one of the two locations.
- The trigger phrase is "dead code" but the verification scope is a single file — dead-code claims require cross-project grep because a symbol can be re-exported, dynamically resolved (Python `getattr`, TS barrel imports), or called from tests.

**Keep the finding** only when the evidence carries either (1) the command + its representative output, or (2) file:line citations that are themselves directly checkable by the human reviewer in a few seconds.

**Canonical failure this gate catches.** A sub-agent claims `"ERROR_CODE_MAP has zero reads; delete it"` based on reading one file. The map is actually read at `main.ts:1129-1130` in the same file it was declared in — a miss the sub-agent would have caught had it been required to paste the grep output (which would have shown `"main.ts:111:const ERROR_CODE_MAP"` AND `"main.ts:1129: errorCode in ERROR_CODE_MAP"` together). The rule: paste the search output, don't summarize it.

### Output requirement — `evidence` field

Every finding at **`blocker` or `critical` severity MUST include a non-empty `evidence` field** (one to three lines) explaining how the failure is reachable in actual use — the concrete trigger input, the observable wrong behavior, and, where relevant, the trust-boundary argument that Gate 2 checked.

- **`warning`** findings SHOULD include `evidence` when non-obvious.
- **`suggestion`** findings MAY include `evidence` but it is not required.

The orchestrator rejects any `critical` or `blocker` finding missing the `evidence` field and returns it to the sub-agent with the instruction: *"Either supply concrete reachability evidence or downgrade / drop the finding per §Finding Suppression Gate."*

### Anti-rationalization (over-flagging direction)

This table is the mirror of the Call-Graph Discipline anti-rationalization table. That one counters "I want to drop this finding"; this one counters "I want to flag this finding" — the bias introduced by the dimensional framework.

| Thought | Reality |
|---------|---------|
| "The input *could* be malformed if an attacker controls it" | Check Gate 2. Internal / trusted / type-checked input sources do not have an attacker. The attack scenario is fictional. Drop. |
| "I haven't found anything in D8 / D11 / D13 yet — I should produce something" | Empty dimensions are valid. Gate 4. Filling a dimension with marginal findings to show effort is the primary cause of over-flagging. Move on. |
| "This is inconsistent with how the sibling module does it" | Inconsistency is a `warning`, not a `critical`, unless the inconsistency itself produces a wrong observable behavior. Pure pattern divergence is `warning` at most. Gate 3 rule 2. |
| "The fix is one line — might as well flag it" | Fix effort does not determine severity. A one-line fix to a non-bug is still a non-bug. If you can't name the observable failure, drop. |
| "If I phrase the description carefully, the finding sounds plausible" | If you need "could theoretically" or "in case someone" to make it sound plausible, it failed Gate 1. Drop or downgrade. |
| "The code doesn't validate this input — that smells wrong" | Lack of validation is only a finding if (Gate 2) the input is genuinely external AND (Gate 1) a malformed input is reachable in actual use. Internal type-checked call sites do not need runtime validation. |
| "Patterns A and B are mixed in this file — that's a code smell" | A code smell is not a bug. Without a concrete observable failure, `suggestion` at most — often drop. |
| "`yaml.dump` instead of `yaml.safe_dump` is a known footgun" | Footgun-awareness is not the same as a bug. If `metadata` in this codebase is built from primitives under the project's invariants, `yaml.dump` produces the same output as `safe_dump`. Findings of the form "if the codebase ever does X, Y would break" are Gate 1 failures. Drop unless the codebase actually does X. |
| "Non-atomic file write — what if the process crashes mid-write" | For a developer tool generating source files for local dev, a partial file on crash is a rerun-and-fix problem, not a correctness bug. Flag only when the artifact is load-bearing in production (data files, DB state, append-only logs). |
| "The method ignores the `ctx` / `cancellation` / `deadline` parameter" | Only a finding if ignoring it produces observable wrong behavior (hung request, leaked resource). If the method completes in microseconds and cancellation is cosmetic, drop or `suggestion`. |
| "Module A does X, module B does Y — that's inconsistency" | Not every difference is a bug. Different modules often serve different logical roles (different trust boundaries, different lifecycle positions, different caller contracts). Inconsistency only matters if it produces divergent **observable behavior** (different caller results, different error handling semantics, test gap). Pure pattern divergence with identical observable behavior is noise — drop. Contract-symmetry pre-flight required before flagging as a cross-module consistency issue. |
| "This is a style / readability improvement — at worst a `suggestion`" | Only if the benefit is concrete and observable: removes dead code, clarifies a non-obvious invariant, eliminates duplication that has drifted. "Might be clearer", "could be simpler", "consider using X", "for readability" are preferences, not findings. If you cannot name the concrete benefit in one line, **drop** — the orchestrator's suggestion-level concrete-benefit check will drop it anyway; pre-empt by not emitting. |
| "I'm going to downgrade this from critical to warning to be safe" | Downgrade-and-keep was the old policy and it failed: noise relocated from `critical` into `warning`/`suggestion` where no further gate ran. The new policy is: speculative phrasing → **DROP at any severity**; warning without named downside → **DROP**; warning with unverified factual claim → **DROP (Gate 5)**; suggestion without named benefit → **DROP**; suggestion that is pure nitpick → **DROP**. If the finding survives a drop check, keep its original severity; if it would only survive after downgrade, it would not have survived the lower-severity drop check either — so drop it now. |
| "I'll write 'zero references' / 'dead code' / 'only used in foo.ts' based on what I remember seeing while reading" | Gate 5 failure. Memory is not evidence. If the claim is falsifiable ("zero", "never", "only", "duplicates"), `evidence` MUST paste the actual `grep -rn <symbol>` output (or equivalent) covering the full repo — not a single file, not a summary sentence. Without the pasted command+output, the finding is DROPPED. "Zero references in the file I read" is not a zero-reference claim; it's a reading bias. |
| "The symbol is only defined here, so it must be dead" | Definition without caller-discovery is incomplete. A symbol may be: (a) re-exported through a barrel (`index.ts`, `__init__.py`, `mod.rs pub use`), (b) dynamically resolved (Python `getattr`, TS `import()`, Go reflection), (c) referenced only from tests (which some greps exclude by default), (d) used by an external consumer (SDK public API). Before claiming dead code, grep the full repo including tests, and sanity-check the exports surface. Without that, drop. |
| "I found three similar issues in the same file — I'll write three separate suggestions" | No. At orchestrator validation #7 (same-theme consolidation), ≥3 suggestions with the same `(file, theme)` are merged into one themed bullet (extra ones dropped). Emit one consolidated suggestion up front with a list of sites — that is the on-target format. Themes include: renaming, format-consistency, error-message-casing, logging-prefix, null-check-style, iteration-style. |
| "It's just a rename for clarity — that's a legitimate suggestion" | Pure rename-for-clarity is a preference, not a finding. Drop unless the current name creates a concrete bug-producing ambiguity (e.g., two symbols with near-identical names that have been confused by a past commit, or a name that actively mis-describes behavior such as `isEnabled` that returns `false` when enabled). If the best justification is "the new name reads better", drop. |
| "`apcore-cli` binary collides with another tool on $PATH — warning-worthy" | Binary-name collisions between sibling projects are a packaging/distribution concern, not a code review finding. Max severity: `suggestion`, and only if the review scope includes packaging. Flag as warning only if the collision demonstrably breaks a documented user flow. |

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
- **MANDATORY post-analysis instruction:** *"After applying dimensions and BEFORE writing any finding into the output YAML, route every candidate finding through §Finding Suppression Gate (Gate 1 Reachability, Gate 2 Trust Boundary, Gate 3 Severity Calibration, Gate 4 Quota Avoidance, **Gate 5 Factual Verifiability**) in the parent SKILL.md. Drop speculative findings whose trigger starts with 'could theoretically' / 'if X ever happens' / 'in case someone'. Drop security / defensive-gap findings whose input source is internal/trusted for this project's threat model. Downgrade design-preference 'critical' findings to `warning`. Accept empty dimensions as a valid result — do NOT fabricate marginal findings to fill a dimension. **Any finding asserting a falsifiable claim about the codebase ('zero references', 'never called', 'dead code', 'only used in X', 'duplicates Y', 'N lines exceed Z') MUST paste the actual verification artifact into `evidence` — the full command used (grep/rg/equivalent) AND its matched-line output, OR explicit file:line citations. Paraphrases like 'grep returns only the declaration' are insufficient — the output itself must be visible. Dead-code claims require cross-directory grep (src + tests). Findings missing the artifact are dropped by Gate 5.** Every `critical` and `blocker` finding MUST include a non-empty `evidence` field explaining the concrete reachable trigger. Before emitting a suggestion, check the nitpick blocklist — pure rename-for-clarity, style swap without named downside, extract-helper for <3 lines, formatting/casing consistency, comment-for-self-documenting-name, binary/packaging name collisions are all dropped at orchestrator validation step 5; pre-empt by not emitting. Prefer consolidating ≥3 same-(file,theme) suggestions into one themed entry — individual emissions will be merged at validation step 7 anyway."*
- Instructions to review across all applicable dimensions (empty dimensions are valid — see Gate 4)
- The severity level definitions (blocker / critical / warning / suggestion — strict, per the SKILL.md severity table)
- Instruction: **"For each issue, specify severity, file path, line number/range, what's wrong, and how to fix it. Use the Review Comment Formula: Problem → Why it matters → Suggested fix. When the issue was discovered via the call graph (e.g., a missing validation call, a skipped state mutation, an unguarded external input), reference the relevant METHOD_CHAINS entry in the description. For critical/blocker findings, the `evidence` field MUST show: (a) the concrete input that triggers the failure, (b) the observable wrong behavior, and (c) for D2/defensive-gap findings, the trust-boundary argument per Gate 2."**

**Review dimensions to apply:** Follow [Dimension Application Rules](#dimension-application-rules). **Apply dimensions AGAINST the call graph, not against the surface method body. Route every finding through §Finding Suppression Gate before emission.**

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
- **MANDATORY post-analysis:** route every candidate finding through §Finding Suppression Gate (Gates 1-5) before writing it into the YAML output. Specifically: drop speculative ("could theoretically", "if X ever happens") findings (Gate 1); drop D1/D2 findings whose input source is internal/trusted under this project's threat model (Gate 2); max-severity-`warning` for design-preference or cross-module-inconsistency findings (Gate 3); empty dimensions are a valid result — do NOT fabricate marginal findings (Gate 4); **any finding asserting a falsifiable codebase fact ("zero references", "never called", "dead code", "only used in X", "duplicates Y", "N lines exceed Z") MUST paste the actual verification artifact (full grep/rg command AND its matched-line output, OR explicit file:line citations) into `evidence` — paraphrases are insufficient; dead-code claims require cross-directory grep covering src + tests (Gate 5)**. Every `critical`/`blocker` finding MUST include a non-empty `evidence` field. Pre-empt the orchestrator's nitpick blocklist (step 5) and suggestion budget (step 6) by not emitting: pure rename-for-clarity, style swap without named downside, extract-helper for <3-line duplication, formatting/casing consistency, comment-for-self-documenting-name, binary/packaging naming. When ≥3 suggestions share the same `(file, theme)`, emit ONE themed suggestion listing every site instead of individual entries.
- **Intra-module dimensions to apply:** D1 (Functional Correctness), D2 (Security), D3 (Resource Management), D4 (Code Quality), D6 (Performance), D8 (Error Handling), D9 (Observability) — applied against the chain INCLUDING tier-2 inlined steps (a D1 defensive gap inside a tier-2 callee IS reported by this agent, subject to Gate 2)
- **Do NOT apply:** D5, D7, D10-D15 — these are handled in the cross-module pass
- The severity level definitions (blocker / critical / warning / suggestion — per SKILL.md severity table, strictly enforced by Gate 3)
- Return format: **Per-Module sub-agent format** (see `references/sub-agent-format.md` §Per-Module format). The output must include `primary_files` (same as input), `tier2_files` (the subset of `in_diff_files` actually opened for tier-2 expansion), and `METHOD_CHAINS` with top-level entries only for public symbols in `primary_files`.
- Instruction: *"Return ALL issues found in chains rooted at YOUR module's public symbols — including issues discovered via tier-2 inlined steps from cross-module callees — that SURVIVE the §Finding Suppression Gate. When a finding lives in a tier-2 inlined step, set the issue's `file` to the tier-2 callee's file (not your module's file). Do not self-filter or defer cross-module concerns — the cross-module agent handles CONSISTENCY across modules, but defensive gaps visible in your chain are yours to flag even if they live in someone else's file. For every critical/blocker finding, the `evidence` field must show the concrete reachable trigger and observable wrong behavior."*

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
- The severity level definitions (blocker / critical / warning / suggestion — per SKILL.md severity table, strictly enforced by Gate 3)
- **MANDATORY post-analysis:** route every candidate finding through §Finding Suppression Gate (Gates 1-5). Cross-module consistency and second-order findings are subject to Gate 2 (a "missing guard" in module B is only a bug if the underlying input is genuinely external per the project's threat model) and Gate 3 (pure convention divergence without observable wrong behavior is `warning` at most, not `critical`). **Gate 5 applies to every cross-module/D15 finding that claims "duplicates Y", "parallel implementation", "reimplements" — the evidence MUST cite both locations with file:line, not just name the pattern.** Empty sections are valid — do not fabricate findings to fill the cross-module template. Every `critical`/`blocker` finding MUST include a non-empty `evidence` field.

**Dimensions to apply (cross-module scope):**
- **D5** (Architecture & Design) — layer boundary violations, circular deps, coupling across the full module set
- **D7** (Test Coverage) — coverage gaps across the full feature scope, test files for each module
- **D10–D13** (Standards, Backward Compat, Maintainability, Dependencies)
- **D15** (Simplification & Anti-Bloat) — cross-module duplicate detection requires the full picture; per-module agents cannot catch parallel implementations across file boundaries

**CROSS_MODULE_CONSISTENCY — apply all five checks (findings subject to §Finding Suppression Gate):**

**Contract-symmetry pre-flight (MANDATORY for every pattern below).** Before flagging any inconsistency, the sub-agent MUST verify the two modules have symmetric contracts: same data-class shape, same lifecycle position, same trust boundary, same caller expectations. Modules that *look* structurally similar but serve different logical roles (one handles user input, one handles constants; one is public API, one is an internal helper; one is invoked at request time, one at startup) are NOT subject to consistency checks — their differences are intentional. If contract symmetry cannot be demonstrated in one line, **drop the finding** — do not flag as warning. This pre-flight exists to prevent the common failure: "A and B look similar, A has guard X, B does not, therefore B is buggy" — the assumption is false whenever A and B serve different roles.

1. **Coerce/guard pattern:** If module A guards `entry.get("key", default)` on dict external inputs, do all sibling modules with structurally equivalent dict-subscript external inputs follow the same pattern? Flag inconsistency as `critical` **only if the underlying input is genuinely external per Gate 2 AND contract symmetry holds**; otherwise `warning` (pure convention divergence) or drop.
2. **Traceback preservation:** If module A uses `raise X from e` or passes `exc_info=True` in exception logging, are all modules in the diff consistent? Flag inconsistency as `warning` **only when** (a) contract symmetry holds and (b) the sub-agent names the observable downside — lost root-cause info when the exception actually fires, with the exception path demonstrably reachable. Pure stylistic divergence (one module uses `from e`, one doesn't, but both are never logged or surfaced to a debug tool) → drop.
3. **Re-export completeness:** For every new public symbol introduced in a submodule, verify it appears in the package `__init__.py` / `index.ts` / `__all__` if the project re-exports its API surface. Flag missing re-exports as `warning` **only when** the sub-agent demonstrates at least one external consumer (outside the submodule) that would need the symbol from the top-level package — grep for imports of other symbols at the top level; if nothing imports from the top level for this submodule's public API, re-export is not a convention. New internal symbols that have no external caller → drop (not API surface).
4. **Error handling convention:** Same error base class hierarchy and chaining approach used across all modules? Flag deviation as `warning` **only when** (a) contract symmetry holds and (b) the sub-agent names how the deviation causes a concrete downstream handling failure (e.g., a `except ProjectError` catch block elsewhere in the codebase will miss the deviating module's errors). Pure class-hierarchy aesthetics with no caller consequence → drop.
5. **Defensive coding depth:** If module A added input validation guards for a specific data path, are all modules with structurally equivalent data paths at the same validation depth? Flag depth mismatch as `critical` **only when the input is genuinely external per Gate 2 AND contract symmetry holds**; otherwise `warning` or drop.

**SECOND_ORDER_REVIEW — active prevention of D-series ("whack-a-mole") bugs:**

For each fix pattern visible in the diff (identifiable from per-module METHOD_CHAINS + intra-module findings):
1. Extract the fix pattern (e.g., "coerce non-dict display surface values", "snapshot sys.path before exec_module", "preserve traceback on scan failure", "emit `suggested_alias` in serializer output")
2. Identify all code paths in OTHER modules in the diff that handle structurally similar data flows
3. Verify the same fix has been applied to each structurally similar path
4. If the fix is missing in any sibling module, emit a `critical` finding **(subject to Gate 2 — if the input is internal/trusted under the project's threat model, DROP the finding entirely; if the input is genuinely external AND contract-symmetry holds between the modules per §CROSS_MODULE_CONSISTENCY pre-flight, keep as `critical`; downgrading to `warning` without a named observable downside is noise and will be dropped by Step 4F validation #4 anyway)**: *"Fix pattern applied in {module_A} was not propagated to {module_B} — structural parity violation. Pattern: {description}. Expected location: {file:line estimate}. Evidence: {concrete reachable trigger showing the gap matters}."*

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
- The severity level definitions (blocker / critical / warning / suggestion — per SKILL.md severity table, strictly enforced by Gate 3)
- Explicit instruction: **"Read every source file. Review the code itself — its logic, structure, correctness, and quality. Reference documents are only used as criteria for the consistency check, not as the subject of review."**
- **MANDATORY pre-analysis instruction:** *"Before applying any review dimension, read every source file in full and build a call graph for every public method / exported function / entry point in those files. Enumerate — for each — the helpers it calls (to leaves within the reviewed scope), the validations it performs, the state mutations it executes, the errors it raises, and its external-input paths. Output this as the `METHOD_CHAINS` section per `references/sub-agent-format.md`. Only after producing METHOD_CHAINS may you apply dimensions. In bare mode, use the method's name, signature, and public-API promises as the internal consistency check target. See the §Call-Graph Discipline section of the parent SKILL.md for the full protocol."*
- **MANDATORY post-analysis instruction:** *"After applying dimensions and BEFORE writing any finding into the output YAML, route every candidate finding through §Finding Suppression Gate (Gate 1 Reachability, Gate 2 Trust Boundary, Gate 3 Severity Calibration, Gate 4 Quota Avoidance) in the parent SKILL.md. Determine the project's threat model first — for dev tools / code generators / linters reading the developer's own files, the trust boundary does not include those files. Drop speculative findings. Drop D1/D2 findings whose input is internal/trusted. Downgrade design-preference `critical` findings to `warning`. Accept empty dimensions. Every `critical`/`blocker` finding MUST include a non-empty `evidence` field showing a concrete reachable trigger and observable wrong behavior."*
- Instruction: **"For each issue, specify severity, file path, line number/range, what's wrong, and how to fix it. Use the Review Comment Formula: Problem → Why it matters → Suggested fix. For critical/blocker findings, the `evidence` field MUST show: (a) the concrete input that triggers the failure, (b) the observable wrong behavior, and (c) for D2/defensive-gap findings, the trust-boundary argument per Gate 2."**

**Review dimensions:** All applicable dimensions. Apply against the call graph, not surface method bodies. **Route every finding through §Finding Suppression Gate before emission.**

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
- **§Finding Suppression Gate post-analysis instruction (same as 3F.4b)** — every finding routed through Gates 1-4 before emission; every `critical`/`blocker` requires `evidence`
- Applies D1, D2, D3, D4, D6, D8, D9 against chains INCLUDING tier-2 inlined steps, with findings subject to Gate 2 (trust boundary for D1 defensive-gap and D2 findings)
- Returns Per-Module sub-agent format (see `references/sub-agent-format.md` §Per-Module format)

Wait for all per-module sub-agents to complete before proceeding.

#### 3P.4 Cross-Module Association Review (Project Mode)

Same protocol as 3F.5, with the following adjustments:

- Instead of Plan Consistency, apply the appropriate **Consistency** check based on `reference_level`:
  - **planning-backed** → Plan Consistency across the full aggregated method chain set
  - **docs-backed** → Documentation Consistency
  - **bare** → Skip consistency; still apply all five CROSS_MODULE_CONSISTENCY checks and SECOND_ORDER_REVIEW
- All five CROSS_MODULE_CONSISTENCY checks (coerce/guard, traceback, re-export, error convention, defensive depth) — **findings subject to §Finding Suppression Gate**, especially Gate 2 (a missing guard is only a bug when the input is genuinely external)
- SECOND_ORDER_REVIEW (same as 3F.5) — **subject to §Finding Suppression Gate**
- D5, D7, D10–D15 — **subject to §Finding Suppression Gate Gate 4 (empty dimensions are valid; do not fabricate marginal findings)**

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

**Suppression-Gate validation (after merge, before display, both paths):**
1. **Evidence presence (critical/blocker):** For every issue at `critical` or `blocker` severity, verify `evidence` is present and non-empty (more than 10 characters of meaningful content — not "see description" or "TBD"). If any critical/blocker is missing evidence, **reject and re-invoke the originating sub-agent** with the message: *"The following critical/blocker findings are missing required `evidence` per §Finding Suppression Gate: [list]. Either supply concrete reachability evidence (the input that triggers the failure + the observable wrong behavior + the trust-boundary argument for D2) or downgrade / drop the finding."* Retry once per agent; after second failure, the orchestrator MUST automatically downgrade those findings to `warning` and append a `[Auto-downgraded: missing evidence]` marker to their description.
2. **Speculative-phrase scan (ALL severities — DROP, do not downgrade):** Scan EVERY finding's description — at `blocker`, `critical`, `warning`, AND `suggestion` — for the speculative tells (`could theoretically`, `if .* ever`, `in case someone`, `potentially might`, `non-deterministic`, `might be nicer`, `smells wrong`, `feels off`, `consider .* just in case`). **DROP each matching finding entirely** — do NOT downgrade-and-keep. Track the drop count by severity and surface it in the report summary. Rationale: the previous "downgrade one level" policy merely relocated noise from `critical`/`warning` into `warning`/`suggestion` where no further gate ran; dropping is the only action that actually cleans the report.
3. **Trust-boundary check on D2/defensive-gap (critical/blocker):** For every critical or blocker in the SECURITY (D2) section or any "missing guard / defensive gap" finding in FUNCTIONAL_CORRECTNESS (D1), verify `evidence` references a genuinely external input source (network / untrusted user / cross-tenant / third-party API / uploaded file). If `evidence` describes only an internal/trusted source (project's own files, hard-coded config, type-checked function arguments) and the project type is `library` / `cli` / `unknown`, auto-downgrade to `warning` with marker `[Auto-downgraded: internal trust boundary]`. (For `frontend` / `backend` / `fullstack` projects, do NOT auto-downgrade — these often face genuinely untrusted user input and the sub-agent's classification of "internal" deserves more scrutiny than the orchestrator can provide; surface as-is and let the human reviewer decide.)
4. **Warning-level observable-downside check (DROP rule):** For every `warning`-severity finding that SURVIVED step 2, verify its description OR `evidence` explicitly names the observable downside — divergent caller behavior, concrete test failure mode, specific maintenance cost with example, or a missing guard whose input source is genuinely external per Gate 2. Findings that merely report pattern/style divergence (*"module A uses X, module B uses Y"*, *"inconsistent with sibling writer"*) with NO named observable downside are **dropped**. Track the drop count and surface it in the report summary. This closes the loophole where the previous validation only scrutinized critical/blocker while warning was a free pass.

   **4b. Factual-claim verification (DROP rule — applies to ALL severities that survived steps 2/3/4, but most often catches warnings and critical/blockers).** Scan every surviving finding's `description` AND `evidence` for the Gate 5 trigger phrases: `zero references`, `zero reads`, `never called`, `never read`, `never invoked`, `no callers`, `dead code`, `unreachable`, `no-op in practice`, `unused`, `only used in`, `only referenced in`, `only read at`, `sole consumer`, `duplicates\s+\w`, `copy of`, `redeclares`, `parallel implementation`, `reimplements`, `grep (returns|shows|finds)`, `\d+\s+lines?\s+(exceed|is|are|over|far)`, `exceeds?\s+\d+\s+lines?`. When a trigger matches, verify `evidence` contains a **verification artifact**:
   - A `grep` / search command line (pattern: `grep(-rn|-r|--[A-Za-z])?\s+...` OR `rg\s+...` OR `Select-String` OR an explicit file-scan description) **AND** actual matched-line output (at least one line of the form `<path>:<line>:<content>` OR the explicit string `0 matches` / `no matches`), OR
   - Explicit `file:line` citations (pattern `[\w/.-]+:\d+`) listing both (for "duplicates X") the original AND the duplicate, or (for "only used in") the definition AND the grep showing no other uses, or (for "N lines") the start:end line range, or
   - For "dead code" / "unused" claims: the grep output MUST span at least `src/` and `tests/` (or the project's test directory equivalent). A dead-code claim whose evidence is only one file or only one directory is **dropped** — dead-code assertions require cross-project search.

   Findings that make a Gate 5 trigger claim without the required verification artifact are **dropped entirely** (not downgraded — the claim itself is the load-bearing part of the finding; without verification the finding has no substance). Track the count as `n_warning_unverified_claim` (all severities — the name reflects the dominant source). Rationale: this gate exists specifically to prevent the failure mode where a sub-agent asserts *"grep returns only the declaration; zero reads"* as summary and the orchestrator has no way to know the grep was never actually run or was run on too narrow a scope. The only defense is to require the output to be visible in the report.

5. **Suggestion-level concrete-benefit check (DROP rule):** For every `suggestion`-severity finding that SURVIVED steps 2 and 4b, verify its description names a specific, observable benefit — dead code to delete, non-obvious invariant the comment would clarify, concrete duplication to extract. Findings that merely float a preference (*"might be clearer"*, *"could be simpler"*, *"consider refactoring"*, *"for readability"*) with NO named benefit are **dropped**. Additionally, scan for the **nitpick blocklist** — drop the suggestion if its `suggestion`/`description` matches any of:
   - Pure rename-for-clarity: `rename\s+\w+\s+to\s+\w+` (unless description also names a concrete bug-producing ambiguity — past confusion incident, mis-describing name, etc.)
   - Style swap without named benefit: `consider using \w+ instead of \w+`, `prefer \w+ over \w+` without a specific downside of the current choice
   - Extract-helper against trivial duplication: "extract helper" / "DRY" / "dedup" where the duplicated block is `<3` lines OR appears in only 2 sites (single-duplicate extraction almost always adds indirection without a maintenance benefit)
   - Formatting / casing: `WARNING: vs Warning:`, `camelCase vs snake_case`, whitespace — this is linter/formatter territory, not review territory
   - Pure comment-style: "add a comment explaining Y" where Y is described by the code's own name (e.g., "add a comment explaining `validateModuleId`")
   - Binary / packaging / distribution naming: binary-name collisions, npm-scope suggestions, bin script renames — unless the review scope explicitly includes packaging

   Track the drop count as `n_suggestion_nitpick`. Surface in report summary.

6. **Suggestion budget (DROP rule — applied AFTER step 5 nitpick filter).** Compute `budget = max(5, ceil(1.5 × warning_count_post_step_4))`. If surviving `suggestion_count > budget`, rank surviving suggestions by (a) whether they have a cited file:line reference, (b) whether they directly map to a dimension with ≥1 critical/warning elsewhere, (c) earlier file paths in alphabetical order as tie-breaker — and drop the tail that exceeds `budget`. Track drops as `n_suggestion_over_budget`. **Rationale:** a review with 2 warnings and 20 suggestions is signaling "I found little substantive but felt obligated to produce bulk" — the reader experience is noise-dominated. Tying suggestion budget to warning count keeps the report's shape matched to the review's actual signal density. Do NOT apply this rule when `warning_count_post_step_4 == 0` AND `critical_count_post_step_3 == 0` — a review that has nothing else to say may legitimately surface a small set of cleanups (but the budget still caps at 5 in that case).

7. **Same-theme consolidation (MERGE rule — applied AFTER step 6 budget):** Group surviving suggestions by `(file, theme)`. Theme is derived from a keyword match on title/description:
   - `renaming` — matches `rename`, `misleading name`, `confusing name`
   - `format_consistency` — matches `casing`, `whitespace`, `formatting`, `alignment`, `indent`
   - `error_message_style` — matches `error message`, `error string`, `error prefix`, `WARNING:|Warning:`
   - `logging_style` — matches `log level`, `log prefix`, `log format`
   - `null_check_style` — matches `null check`, `undefined check`, `?? vs ||`, `optional chaining`
   - `iteration_style` — matches `for loop vs map`, `.forEach vs for-of`, `reduce`
   - `import_style` — matches `import order`, `barrel import`, `named vs default import`

   When a `(file, theme)` group has ≥3 suggestions, merge them into ONE themed suggestion whose description lists every site (file:line list) and drops the individual entries. Track the count of merged-away entries (original count minus 1 per merged group) as `n_suggestion_consolidated`. Do NOT merge cross-file themes — a theme crossing files often indicates a legitimate cross-cutting concern that deserves its own warning-level consideration, not consolidation.

**Report Health computation (after Suppression-Gate validation, before display):**

Compute four health metrics from the merged findings, then derive a single verdict.

**Definitions:**
- `top_pre_downgrade` = number of findings that were `critical` or `blocker` BEFORE the Suppression-Gate auto-downgrade pass ran (i.e., includes findings that were subsequently downgraded). Track this count separately during the auto-downgrade pass.
- `top_post` = `blocker_count + critical_count` after auto-downgrade.
- `n_auto_downgrades` = `n_missing_evidence + n_trust_boundary` — only the TWO validation steps that actually downgrade (steps 1 and 3). Speculative-phrase matches are now DROPS, not downgrades, and are tracked in `dropped_total` instead.
- `n_speculative` = count of findings dropped by step 2 (speculative-phrase scan, across all severities).
- `n_warning_no_downside` = count of warnings dropped by step 4 (no named observable downside).
- `n_warning_unverified_claim` = count of findings dropped by step 4b (factual-claim without verification artifact — most commonly warnings but applies to all severities).
- `n_suggestion_no_benefit` = count of suggestions dropped by step 5's concrete-benefit sub-check (no named concrete benefit).
- `n_suggestion_nitpick` = count of suggestions dropped by step 5's nitpick-blocklist sub-check (rename-for-clarity, style swap, trivial-extract-helper, formatting, self-documenting-name comment, packaging-name).
- `n_suggestion_over_budget` = count of suggestions dropped by step 6 (budget overflow beyond `max(5, 1.5 × warning_count_post_step_4)`).
- `n_suggestion_consolidated` = count of suggestions merged away by step 7 (same-`(file, theme)` groups of ≥3 collapsed to one themed bullet; the merged-away count is `original_count − 1` per group).
- `dropped_total` = `n_speculative + n_warning_no_downside + n_warning_unverified_claim + n_suggestion_no_benefit + n_suggestion_nitpick + n_suggestion_over_budget + n_suggestion_consolidated`.
- `raw_findings_count` = `total_issues + dropped_total` — the sub-agent's raw output count BEFORE any drop.
- Invariants: `top_pre_downgrade = top_post + n_auto_downgrades`; `raw_findings_count = total_issues + dropped_total`.

**Metrics:**
1. **Finding density** = `total_issues / max(LOC_reviewed / 100, 1)` — issues per 100 LOC reviewed. `LOC_reviewed` = sum of lines across `primary_files` (deduplicate when a file appears in multiple module groups; count each file once).
2. **Critical share** = `top_post / max(total_issues, 1)` — fraction of findings still at top severity after the gate.
3. **Auto-downgrade share** = `n_auto_downgrades / max(top_pre_downgrade, 1)` — fraction of would-be top-severity findings that the gate had to lower.
4. **Drop share** = `dropped_total / max(raw_findings_count, 1)` — fraction of raw candidate findings that the gate dropped (from speculative-phrase scan, warning observable-downside check, and suggestion concrete-benefit check combined). `raw_findings_count = total_issues + dropped_total`; `dropped_total` is the sum of drops from validation steps 2, 4, and 5.

**Per-metric flag rules (each metric independently raises a flag):**

| Metric | Flag raised when | Flag name |
|---|---|---|
| Finding density | `> 2.0` | **noisy** |
| Critical share | `> 0.10` (10%) AND `total_issues ≥ 10` (small-report exemption: under 10 total findings, the share is too sensitive to be meaningful) | **inflated** |
| Auto-downgrade share | `> 0.30` (30%) AND `top_pre_downgrade ≥ 3` (small-report exemption: under 3 top-severity candidates, the share is too sensitive) | **gated** |
| Drop share | `> 0.40` (40%) AND `raw_findings_count ≥ 10` (small-report exemption: under 10 raw findings, the share is too sensitive) | **fabricating** |

The in-between bands (density 1.0–2.0, critical share 5–10%, auto-downgrade share 15–30%, drop share 20–40%) are advisory only — they do NOT raise a flag, but the report header SHOULD show them with a yellow indicator (⚠) so the user can see borderline conditions. The **fabricating** flag catches sub-agents whose prompt is systematically generating noise the gate then has to remove — if the gate drops >40% of the raw output, the sub-agent is not being careful and the remaining 60% also deserves scrutiny.

**Verdict assembly:**
- **`healthy`** — no flags raised
- Otherwise — comma-joined list of raised flags in this order: `noisy`, `inflated`, `gated`, `fabricating` (e.g., `"noisy,fabricating"`)

Record the verdict and the three numeric metrics in the report header (see `references/report-template.md` §Report Health) and in `state.json` `review.health` (feature mode only — see Step 5F). Persist `top_pre_downgrade` as well so trend analysis across runs can distinguish "gate caught fewer because there were fewer attempts" from "gate caught fewer because the prompt is now better".

Follow the report template in `references/report-template.md` (Feature mode variant).

#### 4F.1 Optional: Save to File (`--save`)

If the user passed `--save` in the arguments, **also** write the report to `{output_dir}/{feature_name}/review.md`. Otherwise, do NOT create the file.

→ Go to Step 5F

---

### Step 4P: Project Mode — Display Report

**Orchestrator validation (before display):**

*Fast path (3P.3a):* Verify `METHOD_CHAINS` covers every public method / exported function in the collected source files. Reject + re-invoke if missing or thin. In project mode the file set can be large; the sub-agent MAY split METHOD_CHAINS into groups-by-file, but total coverage must hit every public symbol. If the sub-agent legitimately cannot cover every symbol within a single response (e.g., 500+ public functions), it MUST explicitly list the un-analyzed symbols in a `METHOD_CHAINS_DEFERRED` block with reason `"scope-too-large"` — this surfaces to the user as: `⚠ {N} public symbols not analyzed due to scope — consider narrowing via --project scope=changes or per-feature review`. Never silently skip.

*Layered path (3P.3b + 3P.4):* Apply the same merge and validation logic as Step 4F layered path — verify per-module METHOD_CHAINS coverage, verify cross-module agent produced CROSS_MODULE_CONSISTENCY and SECOND_ORDER_REVIEW sections, merge all findings, deduplicate by `(file, line, title)`, construct unified REVIEW_SUMMARY. Append a **Cross-Module section** to the report.

**Suppression-Gate validation (after merge, before display, both paths):** Apply the same seven checks as Step 4F:
1. **Evidence presence (critical/blocker)** — every critical/blocker requires non-empty `evidence`; reject and re-invoke originating agent, auto-downgrade after second failure with `[Auto-downgraded: missing evidence]` marker.
2. **Speculative-phrase scan (ALL severities — DROP)** — scan every finding at every severity for the speculative tells (`could theoretically` / `if .* ever` / `in case someone` / `potentially might` / `non-deterministic` / `might be nicer` / `smells wrong` / `feels off`). **Drop matching findings entirely** — do not downgrade-and-keep. Track drops by severity.
3. **Trust-boundary check (critical/blocker)** — auto-downgrade D2/defensive-gap critical/blocker findings whose `evidence` describes an internal/trusted source for `library` / `cli` / `unknown` project types, with `[Auto-downgraded: internal trust boundary]` marker. (Skip auto-downgrade for `frontend` / `backend` / `fullstack` — let humans review those.)
4. **Warning-level observable-downside check (DROP)** — for every surviving `warning`, verify description or `evidence` names the observable downside; pure pattern/style divergence with no named downside is dropped.
   **4b. Factual-claim verification (DROP — all severities)** — when description/evidence contains a Gate 5 trigger phrase (`zero references`, `zero reads`, `never called`, `dead code`, `unused`, `only used in`, `only referenced in`, `duplicates\s+\w`, `reimplements`, `parallel implementation`, `grep (returns|shows|finds)`, `\d+\s+lines?\s+(exceed|is|are)`), require `evidence` to carry a verification artifact (command + output OR file:line citations). Dead-code claims additionally require cross-directory grep (src + tests at minimum). Drop findings without the artifact. Track as `n_warning_unverified_claim`.
5. **Suggestion-level concrete-benefit check (DROP)** — for every surviving `suggestion`, verify a specific, observable benefit is named; preference-only findings (*"might be clearer"*, *"consider refactoring"*) are dropped. Also apply the **nitpick blocklist** — drop suggestions matching: pure rename-for-clarity, style swap without named downside, extract-helper for <3-line duplication, formatting/casing (linter territory), comment-for-self-documenting-name, binary/packaging naming (out of scope). Track as `n_suggestion_nitpick`.
6. **Suggestion budget (DROP)** — `budget = max(5, ceil(1.5 × warning_count_post_step_4))`; rank surviving suggestions (has file:line > maps to a non-empty dimension > earlier path alphabetically) and drop the tail above budget. Track as `n_suggestion_over_budget`. Skip when warnings and criticals are both zero and surviving suggestions ≤ 5.
7. **Same-theme consolidation (MERGE)** — group surviving suggestions by `(file, theme)`; when ≥3 suggestions share a `(file, theme)`, merge into one themed bullet listing every site. Track merged-away entries as `n_suggestion_consolidated`. Themes: renaming, format_consistency, error_message_style, logging_style, null_check_style, iteration_style, import_style. Do not merge across files.

Surface a single summary line in the report noting the number of auto-downgrades AND the number of drops per severity, so users can spot quota-filling, trust-boundary mistakes, or noise generation without reading the full report.

**Report Health computation (after Suppression-Gate validation, before display):** Same four-metric computation as Step 4F (finding density, critical share, auto-downgrade share, drop share) and same verdict thresholds (`healthy` / `noisy` / `inflated` / `gated` / `fabricating`). Record the verdict and metrics in the report header per `references/report-template.md` §Report Health. (Project mode does not write to `state.json`, so the health record only appears in the displayed report.)

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
       "suggestions": 4,
       "health": {
         "verdict": "healthy",
         "finding_density": 1.4,
         "critical_share": 0.16,
         "auto_downgrade_share": 0.0,
         "drop_share": 0.08,
         "loc_reviewed": 850,
         "top_pre_downgrade": 2,
         "top_post": 2,
         "raw_findings_count": 13,
         "auto_downgrades": {
           "missing_evidence": 0,
           "internal_trust_boundary": 0
         },
         "drops": {
           "speculative_phrasing": 1,
           "warning_no_observable_downside": 0,
           "warning_unverified_claim": 0,
           "suggestion_no_concrete_benefit": 0,
           "suggestion_nitpick": 0,
           "suggestion_over_budget": 0,
           "suggestion_consolidated": 0
         }
       }
     }
   }
   ```
   - `health.verdict` is one of `healthy` / `noisy` / `inflated` / `gated` / `fabricating` (or comma-joined when multiple flags apply, e.g. `"noisy,fabricating"`)
   - If `--save` was used, also include `"report": "review.md"` in the review object
   - Persisting `health` enables trend analysis across runs — a rising `auto_downgrade_share` signals that the review prompts need reinforcement; a rising `drop_share` signals the sub-agent is systematically generating noise (speculative / style-only / benefit-less findings) and the prompt needs tightening
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
Report Health: {verdict_emoji_concatenated} {verdict} · density {finding_density}/100 LOC · critical share {critical_share_pct}% · auto-downgrades {n_auto_downgrades} · drops {dropped_total}
{If verdict != healthy, append one block-quote line PER raised flag (in order noisy, inflated, gated, fabricating):}
  ⚠ {flag_name}: {hint per §6.3 Verdict Emoji & Hints}
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
Report Health: {verdict_emoji_concatenated} {verdict} · density {finding_density}/100 LOC · critical share {critical_share_pct}% · auto-downgrades {n_auto_downgrades} · drops {dropped_total}
{If verdict != healthy, append one block-quote line PER raised flag (in order noisy, inflated, gated, fabricating):}
  ⚠ {flag_name}: {hint per §6.3 Verdict Emoji & Hints}
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

#### 6.3 Verdict Emoji & Hints

Use this table for the `Report Health` line (both feature and project mode):

| Flag | Emoji | One-line hint |
|---|---|---|
| (none — `healthy`) | ✅ | (no hint — line ends after the metrics) |
| `noisy` | 🔊 | Density > 2 issues per 100 LOC — likely quota-filling. Re-read findings critically; many may be marginal. |
| `inflated` | 🎈 | Critical share > 10% post-downgrade — severity inflation surviving the gate. Re-check Gate 3 calibration on top findings. |
| `gated` | 🚧 | Auto-downgrade share > 30% — gate caught widespread bypass attempts. Sub-agent prompt may need reinforcement. |
| `fabricating` | 🛑 | Drop share > 40% — the gate dropped nearly half the raw findings as speculative/style-only/benefit-less. The remaining findings also deserve scrutiny; the sub-agent prompt is systematically generating noise. |

**Multi-flag rendering:** Concatenate emojis in the order `noisy,inflated,gated,fabricating` (e.g., `🔊🛑` for `noisy,fabricating`). Display each flag's hint on its own line below the metrics. Example:

```
Report Health: 🔊🚧🛑 noisy,gated,fabricating · density 3.1/100 LOC · critical share 6% · auto-downgrades 5 · drops 12
  ⚠ noisy: Density > 2 issues per 100 LOC — likely quota-filling. Re-read findings critically; many may be marginal.
  ⚠ gated: Auto-downgrade share > 30% — gate caught widespread bypass attempts. Sub-agent prompt may need reinforcement.
  ⚠ fabricating: Drop share > 40% — the gate dropped nearly half the raw findings as speculative/style-only/benefit-less. The remaining findings also deserve scrutiny; the sub-agent prompt is systematically generating noise.
```
