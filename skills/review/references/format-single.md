# Sub-agent Response Format — Fast-Path Single Agent

Used by the fast-path single agent (Step 3F.4a / 3P.3a) and GitHub PR mode. Covers all 15 dimensions in one response.

**Read `format-common.md` first** — it defines the `evidence` requirements and the `CANDIDATE_INVENTORY` drop ledger used below.

**Tier-2 note.** On the fast path your review scope IS the whole affected-file set — there is no `primary_files` / `in_diff_files` split, so the tier-2 set is empty and the 8-file tier-2 expansion budget never applies to you. Every in-scope callee is tier 1 (inline fully); everything outside the scope is tier 3 (`ext_call` leaf). The three-tier vocabulary below is shared with the layered path; read `Tier 2` there as "not reachable in this role".

**Note:** Feature mode and Project mode have slightly different fields in `REVIEW_SUMMARY` and the final consistency section — see §Consistency Section at the end of this file.

```
METHOD_CHAINS:
# One entry per public method / exported function / entry-point.
# Private helpers do NOT get their own top-level entry — their body steps MUST be inlined into the
# public method's chain via the inlining convention (indent + "helper_name →" prefix in `detail`).
# Treating a call to a same-file private helper as an opaque leaf is a pre-analysis failure.
# Test files are exempt.
- symbol: <ClassName.method_name | function_name | entry_point_name>
  file: <path/to/file.ext>
  line: <start line of the symbol's definition>
  purpose: <one-line statement of what the method SHOULD do — derived from docstring, plan.md, spec, or (bare mode) from the method's name + signature>
  chain:
    # Ordered list of steps the method actually performs, INCLUDING steps inlined from private helpers.
    # Step kinds:
    #   call: <helper_name>           — function/method invocation. Expansion depends on tier:
    #                                    Tier 1 (same-module private helper)  → IMMEDIATELY follow with fully
    #                                                                            inlined body using "  helper →" prefix
    #                                    Tier 2 (cross-module callee in diff) → follow with depth-1 inlined body
    #                                                                            using "  X:Module.method →" prefix
    #                                    Tier 3 (stdlib / third-party / not   → use `ext_call` instead — no expansion
    #                                              in diff)
    #   ext_call: <lib.func>          — LEAF — tier 3 only. stdlib, third-party library, framework, OR private
    #                                    helper defined in a file NOT in the review scope (neither primary nor tier2).
    #   validate: <condition>         — early-return / raise / assert guard
    #   mutate: <target>              — write to state (self.x, map insert, event emit, lock acquire, I/O)
    #   raise: <ErrorType>            — error raised / thrown / returned-as-Err
    #   iterate: <source>             — iteration over external input (argument, deserialized data, plugin output)
    #   subscript: <source>           — indexing/key-access into external input
    #   deserialize: <source>         — parsing of external input (JSON, YAML, pickle, config file)
    #   no_op: <explanation>          — explicit note that something expected was NOT done
    #
    # Optional step kinds (MAY appear when they clarify the chain; orchestrator accepts them):
    #   branch: <condition>           — conditional branch marker (if/else, match arm selection)
    #   return: <value>               — explicit return statement (useful to mark exit paths)
    #   lock: <target>                — lock acquire (a specialization of `mutate` when a RLock/Mutex is the subject)
    #   yield: <value>                — generator yield (context manager __enter__/__exit__ boundaries)
    #
    # THREE-TIER INLINING CONVENTION (per `call-graph-discipline.md`):
    # Tier 1 — same-module private helper: follow `call` with full recursive inlining, "  helper →" prefix.
    #          Two-level nesting: "    HELPER_A → HELPER_B → step" (additional indent per depth).
    # Tier 2 — cross-module callee ALSO in the review scope: follow `call` with DEPTH-1 inlining (top-level
    #          body only, do not recurse deeper), "  X:Module.method →" prefix. The `X:` marker signals the
    #          cross-module boundary crossing.
    #
    #     # Tier 1 example (same-module private helper):
    #     - { kind: call,      detail: "_discover_custom(rootPaths)",                                   line: 257 }
    #     - { kind: call,      detail: "  _discover_custom → custom_discoverer.discover(roots)",        line: 262 }
    #     - { kind: iterate,   detail: "  _discover_custom → for entry in custom_modules",              line: 263 }
    #     - { kind: subscript, detail: "  _discover_custom → entry['module_id'] (unguarded)",           line: 269 }
    #     - { kind: raise,     detail: "  _discover_custom → KeyError uncaught, aborts whole loop",     line: 269 }
    #
    #     # Tier 2 example (cross-module callee in diff, depth-1):
    #     - { kind: call,      detail: "DisplayResolver.resolve(node)",                                 line: 45 }
    #     - { kind: call,      detail: "  X:DisplayResolver.resolve → for surface in node.surfaces",    line: 78 }
    #     - { kind: subscript, detail: "  X:DisplayResolver.resolve → surface['values']  (unguarded)",  line: 82 }
    #     - { kind: raise,     detail: "  X:DisplayResolver.resolve → TypeError if not dict",           line: 85 }
    #     - { kind: ext_call,  detail: "  X:DisplayResolver.resolve → _apply_coerce(surface) [tier3]",  line: 90 }
    #
    # Example for a public method with a straight-line body + one inlined helper:
    - { kind: validate, detail: "id matches ^[a-z][a-z0-9_]*$", line: 45 }
    - { kind: call,     detail: "self._resolve_deps(module)", line: 47 }
    - { kind: call,     detail: "  _resolve_deps → for dep in module.requires", line: 92 }
    - { kind: call,     detail: "  _resolve_deps → self._registry.get(dep)", line: 93 }
    - { kind: raise,    detail: "  _resolve_deps → DependencyError if dep missing", line: 95 }
    - { kind: mutate,   detail: "self._index[id] = module", line: 51 }
    - { kind: mutate,   detail: "self._lowercase_map[id.lower()] = id", line: 52 }
    - { kind: no_op,    detail: "no emit('registered') — spec declares event but chain omits it", line: 53 }
    - { kind: raise,    detail: "DuplicateError when id already in _index", line: 43 }
  chain_completeness: <matches_purpose | partial | suspicious>
  # matches_purpose  — every step implied by `purpose` is present in `chain`
  # partial           — one or more expected steps missing; list them in `gaps`
  # suspicious        — something in `chain` contradicts `purpose` (e.g., public method `discover` doesn't actually register anything)
  gaps:
  # Only populated when chain_completeness != matches_purpose.
  # Each gap must correspond to a D1 (or D3 / D8) finding below — the chain is the evidence, the finding is the verdict.
  - <description of a step that `purpose` implies but `chain` omits, OR a contradiction>
  external_inputs:
  # Every iterate / subscript / deserialize step from `chain` — INCLUDING steps inlined from tier-1 helpers
  # AND tier-2 cross-module callees. A public method's body can look clean while its chain's `external_inputs`
  # is non-empty because of an unguarded subscript/iterate inside a private helper OR inside a cross-module
  # callee that's also in the diff. Both classes are bugs this discipline catches.
  - source: <name>
    guarded: <true | false>
    guard_detail: "<null-check | try/except | type guard | schema | none>"
    via: "<direct | helper_name | X:Module.method>"
    # via values:
    #   "direct"              — iterate/subscript in the public method's own body
    #   "<helper_name>"       — inside a tier-1 inlined private helper
    #   "X:<Module.method>"   — inside a tier-2 inlined cross-module callee (in diff)

# If the sub-agent cannot cover every public symbol in a single response (very large project scope), it MUST list
# the uncovered symbols here instead of silently skipping. The orchestrator surfaces this to the user.
METHOD_CHAINS_DEFERRED:
- symbol: <ClassName.method_name>
  file: <path>
  reason: <scope-too-large | unreadable-source | generated-code | test-file-miscategorized>

CANDIDATE_INVENTORY:
# MANDATORY section header — this is a DROP LEDGER.
# List ONLY candidates you considered and decided NOT to emit.
# Findings you KEEP are NOT listed here — they appear in full in the dimension blocks.
# See §Pre-emission Scratchpad in `format-common.md` for the drop-code enum.
# An empty list is valid (nothing was dropped); the header itself is still required.
- id: <C1 | C2 | ...>
  dimension: <D1 | D2 | ... | D15>
  file: path/to/file.ext
  line: <number or range>
  title: <short title>
  drop_reason: <enum code — NO free text>
  drop_detail: <one line — why this code applies to this candidate>

REVIEW_SUMMARY:
  overall_rating: <pass | pass_with_notes | needs_changes>
  total_issues: <number>
  blocker_count: <number>
  critical_count: <number>
  warning_count: <number>
  suggestion_count: <number>
  merge_readiness: <ready | fix_required | rework_required>
  dimensions_reviewed: <list of dimension IDs reviewed>
  # [Project mode only] reference_level: <planning | docs | bare>

FUNCTIONAL_CORRECTNESS:                              # D1
  rating: <pass | warning | critical>
  issues:
  - severity: <blocker | critical | warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <what's wrong and why it matters>
    suggestion: <how to fix>
    evidence: <REQUIRED for critical/blocker; SHOULD be present for warning when non-obvious. One to three lines: (a) concrete trigger input, (b) observable wrong behavior, (c) trust-boundary argument for D1 defensive-gap findings (per §Finding Suppression Gate Gate 2).>

SECURITY:                                            # D2
  rating: <pass | warning | critical>
  issues: [same structure as D1 — evidence REQUIRED for critical/blocker, must include trust-boundary argument]

RESOURCE_MANAGEMENT:                                 # D3
  rating: <pass | warning | critical>
  issues: [same structure as D1 — evidence REQUIRED for critical/blocker]

CODE_QUALITY:                                        # D4
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <critical | warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <what's wrong and why it matters>
    suggestion: <how to fix>
    evidence: <REQUIRED for critical; SHOULD be present for warning when non-obvious>

ARCHITECTURE:                                        # D5
  rating: <good | acceptable | needs_work>
  issues: [same structure as D4 — evidence REQUIRED for critical]

PERFORMANCE:                                         # D6
  rating: <good | acceptable | needs_work>
  issues: [same structure as D4 — evidence REQUIRED for critical]

TEST_COVERAGE:                                       # D7
  rating: <good | acceptable | needs_work>
  coverage_gaps:
  - severity: <critical | warning | suggestion>
    file: path/to/source.ext
    description: <what scenario is untested>
    evidence: <REQUIRED for critical: which observable behavior is at risk because the path is untested>

ERROR_HANDLING_AND_OBSERVABILITY:                     # D8 + D9
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    category: <error_handling | logging | metrics | tracing>
    title: <short title>
    description: <what's wrong and why it matters>
    suggestion: <how to fix>
    evidence: <SHOULD be present for warning when non-obvious; OPTIONAL for suggestion>

MAINTAINABILITY_AND_COMPATIBILITY:                    # D10 + D11 + D12 + D13
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    category: <standards | backward_compat | tech_debt | dependencies>
    title: <short title>
    description: <what's wrong and why it matters>
    suggestion: <how to fix>
    evidence: <SHOULD be present for warning when non-obvious; OPTIONAL for suggestion — but REQUIRED at any severity for findings making factual claims (Gate 5)>
    # Suggestion CONSOLIDATION (parent SKILL.md Step 4F validation #7):
    # When ≥3 suggestions share the same (file, theme) — renaming, format_consistency,
    # error_message_style, logging_style, null_check_style, iteration_style, import_style —
    # emit ONE themed entry listing every site, NOT individual entries. The orchestrator
    # merges non-consolidated entries automatically, but pre-consolidating avoids noise.
    # Example themed entry:
    #   severity: suggestion
    #   file: src/output.ts
    #   line: multiple
    #   title: "Null-check style inconsistency across output.ts"
    #   description: "8 call sites mix `?? 'default'` with `|| 'default'` for the same kind of null-or-empty-string check. Theme: null_check_style. Sites: src/output.ts:86, :105, :142, :188, :211, :244, :270, :318."
    #   suggestion: "Standardize on `?? 'default'` (nullish-only) to avoid treating valid empty strings as missing."

ACCESSIBILITY:                                       # D14 (frontend/fullstack only)
  rating: <good | acceptable | needs_work | skipped>
  issues:
  - severity: <warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <what's wrong and why it matters>
    suggestion: <how to fix>
    evidence: <SHOULD be present for warning when non-obvious>
```

## Consistency Section (mode-specific)

### Feature Mode — `PLAN_CONSISTENCY`

```
PLAN_CONSISTENCY:
  criteria_met: <X/Y>
  unmet_criteria:
  - <criterion not met>
  scope_issues:
  - <unplanned additions or missing planned features>
```

### Project Mode — `CONSISTENCY`

```
CONSISTENCY:
  type: <plan_consistency | doc_consistency | skipped>
  rating: <good | acceptable | needs_work | N/A>
  criteria_met: <X/Y> (if applicable)
  unmet_criteria:
  - <criterion not met>
  scope_issues:
  - <unplanned additions or missing documented features>
```
