# Call-Graph Discipline (Mandatory Sub-Agent Pre-Analysis)

**Before applying any dimension, the review sub-agent MUST build a call graph for every public method in the review scope.** This is a procedural requirement, not a new dimension. It exists because surface-level reading of a method body is structurally blind to a class of bugs: a method may look complete, have the right signature, match the declared plan/spec, yet silently skip a validation call, lack a null-guard on external input, or omit an expected state mutation. These bugs are visible in the call graph and invisible in the method body alone.

---

## Three-tier expansion rule

The graph must enumerate, for every public method:

### Tier 1 — Same-module private helpers: FULL recursive inlining

When a public method calls a private helper defined in the same reviewed scope (same file, or a nearby private module within the same module group), you MUST open that helper and **inline its steps** (validations, mutations, raises, iterates, subscripts, calls-to-further-helpers) into the public method's chain. Recurse to leaves. Do NOT leave a private same-scope helper as an opaque `call` step — that hides exactly the bugs this discipline exists to catch.

### Tier 2 — Cross-module callees that are ALSO in the review scope: DEPTH-1 expansion

When a public method calls a function/method defined in a **different module group BUT still part of the current review scope** (i.e., the callee's file is also in the diff / affected-files list), you MUST open that callee's file, read the called method's body, and **inline its top-level steps at depth 1** (direct validations, mutations, raises, iterates, subscripts, and immediate sub-calls to its own private helpers — but do NOT recurse deeper into the callee's private helpers beyond one level). Mark these inlined steps with the `X:` prefix and the fully-qualified callee name to make the cross-module boundary visible:

```
- { kind: call,      detail: "DisplayResolver.resolve(node)", line: 45 }
- { kind: call,      detail: "  X:DisplayResolver.resolve → for surface in node.surfaces", line: 78 }
- { kind: subscript, detail: "  X:DisplayResolver.resolve → surface['values']  (unguarded)", line: 82 }
- { kind: raise,     detail: "  X:DisplayResolver.resolve → TypeError if surface not dict", line: 85 }
```

Rationale: a cross-module callee that is itself being modified in this diff is part of the same logical change unit as the caller. If `DisplayResolver.resolve` has an unguarded subscript, a caller that invokes it over external input is exposed to that bug. Treating the callee as an opaque `ext_call` re-creates the very blind spot the discipline exists to close.

### Tier 3 — Leaves (NO expansion)

- Stdlib calls (`json.loads`, `os.path.join`)
- Third-party library calls (`requests.get`, `pydantic.BaseModel.model_validate`)
- Framework calls (`Flask.route`, `React.useState`)
- Private helpers / methods defined in a file that is **NOT in the current review scope** (untouched code outside the diff)

Represent all tier-3 steps as `ext_call` with no further expansion.

---

## What the graph must enumerate

For every public method:

1. **Every step in the execution path** — including tier-1 recursive inlining and tier-2 depth-1 cross-module inlining per the rule above.
2. **Every validation performed anywhere in the chain** (early `if/raise`, `assert`, `match`, type guards, schema validation, Protocol checks, `isinstance`, `instanceof`) — including validations inside all inlined bodies.
3. **Every state mutation anywhere in the chain** (writes to `self.x` / `this.x`, inserts into maps/sets/lists, event emissions, lock acquisitions, external I/O) — including mutations inside all inlined bodies.
4. **Every error raised anywhere in the chain** (`raise`, `throw`, `return Err`, `return nil, err`) — including raises inside all inlined bodies.
5. **Every external input path anywhere in the chain** (iteration over arguments, subscript/indexing into external data — especially data returned by plugin/discoverer/factory callbacks, deserialization of user/plugin/config input, network reads) — including paths inside all inlined bodies. This is where defensive-gap bugs live and they are almost always inside private helpers OR inside cross-module callees.

## Inlining convention

When inlining a helper's steps into a public method's chain, prefix the `detail` field to preserve the call hierarchy:

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

**The graph is produced as structured output (see `sub-agent-format.md` `METHOD_CHAINS` section)** — the sub-agent shows its work. An empty or missing `METHOD_CHAINS` section means the sub-agent skipped the pre-analysis; the orchestrator MUST reject the report and re-run.

**Why this is procedural, not a dimension.** The graph is an *input* to dimensions D1 (correctness), D3 (resource), D8 (error handling), D15 (anti-bloat), and others — not a finding category itself. Dimensions are applied to the graph, not to the raw method body. Findings that emerge from graph inspection still belong to their natural dimension (e.g., "method skips a validation its docstring promises" → D1; "method exits without releasing a lock it acquired" → D3).

**Scope.** The discipline applies to **every public method of every class, every exported function, and every entry-point / CLI command** in the reviewed files. Private helpers do NOT get their own top-level `METHOD_CHAINS` entry — but their steps (validations, mutations, raises, iterates, subscripts) MUST be inlined into the chain of the public method that invokes them, using the inlining convention above. Stopping expansion at `call: _private_helper` without inlining its body is a **pre-analysis failure**; the orchestrator rejects such chains. Test files are exempt.

---

## Anti-rationalization (under-flagging direction)

This table counters the bias "I want to drop this chain expansion" — skipping inlining to save effort. The mirror table countering "I want to flag this finding" lives in `suppression-gates.md`.

| Thought | Reality |
|---------|---------|
| "The method is only 10 lines, the graph is trivial, skip it" | The Rust `discover_internal` bug in apcore-rust was in a short method. Short methods that skip expected work are exactly what the graph catches — the absence of a call is invisible to surface reading. Always build the graph. |
| "The plan / spec says the method does X, so it does X" | Do not trust the plan. Verify X is actually invoked by reading the chain to its leaves. A common skill-driven bug: the plan says "implement validate_module_id", the impl file adds a `validate_module_id` function, but no caller ever invokes it. |
| "The method calls a well-named helper, the helper must be doing its job" | Never infer behavior from function names. Open the helper and verify. A helper called `validate_foo()` may be a stub, may early-return on a wrong branch, may not actually validate. |
| "This is defensive code for impossible states, D15 says flag it as suggestion" | D15 targets defensive code for states that the type system or upstream invariant actually prevents. Defensive code for **possible** states — external-facing iteration, subscript into user/plugin-supplied dicts, deserialization paths — is D1 territory (functional correctness). Do not downgrade to suggestion when the input source is genuinely external. |
| "No reference document, can't check purpose" | In bare mode you cannot check against a spec, but you can still check **internal consistency**: does the method name imply a contract (`discover`, `register`, `validate`) that the chain contradicts? Does the public API promise a return shape that the chain does not produce? Graph inspection still yields signal. |
| "The public method just calls `_private_helper()` — that's one `call` step, chain done" | NO. The most common place for defensive-gap bugs and missing-validation bugs is **inside private helpers** — a public method with a clean three-line body whose private helper does an unguarded subscript into plugin output, or an iterate over possibly-null external data, is the exact case this discipline exists to catch. When a `call` targets a private helper defined in the same reviewed scope, you MUST open it and inline its steps per the inlining convention. "Stop at the first `call` boundary" produces the illusion of a clean chain while the bug hides one level deeper. If your METHOD_CHAINS for a public method is ≤3 steps because its body was "just delegation", you almost certainly skipped inlining — go back and expand. |
| "The method calls into another module — that's cross-module, so it's an `ext_call` leaf" | Only true if the callee is NOT in the current review scope. If the callee's file is **also being modified in this diff**, it is part of the same logical change unit and must be expanded at tier-2 (depth-1) with the `X:` marker. Treating an in-diff cross-module callee as opaque produces exactly the failure mode the layered-review architecture exists to prevent: defensive gaps that straddle module boundaries become invisible to both the per-module agent (didn't open the callee) and the cross-module agent (received only chain summaries, can't re-derive the gap). If `CallerModule.foo()` calls `CalleeModule.bar()` and both files are in the diff, the per-module agent handling `CallerModule` MUST open `CalleeModule.bar` and inline its top-level body. |
