# Sub-agent Response Format

The review sub-agent must return results in the following structured YAML format.

**Note:** Feature mode and Project mode have slightly different fields in `REVIEW_SUMMARY` and the final consistency section. See the mode-specific notes below.

**`METHOD_CHAINS` is MANDATORY and comes first — the orchestrator rejects any response without it.** See the §Call-Graph Discipline section of the parent SKILL.md for the protocol. The sub-agent must produce one `METHOD_CHAINS` entry per public method / exported function / entry-point in the reviewed scope, then apply dimensions against the graph, not against surface method bodies.

**`evidence` field is MANDATORY for every `critical` and `blocker` finding.** See §Finding Suppression Gate in the parent SKILL.md. The orchestrator rejects critical/blocker findings missing `evidence` and (after one re-invoke) auto-downgrades them with a `[Auto-downgraded: missing evidence]` marker. `evidence` SHOULD be present for `warning` findings when non-obvious; OPTIONAL for `suggestion`. The field must show: (a) the concrete input/condition that triggers the failure, (b) the observable wrong behavior, and (c) for D2 / D1-defensive-gap findings, the trust-boundary argument per Gate 2.

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
    # THREE-TIER INLINING CONVENTION (per §Call-Graph Discipline):
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
    evidence: <SHOULD be present for warning when non-obvious; OPTIONAL for suggestion>

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

---

## Per-Module Sub-agent Format

Used by each parallel per-module agent in the layered review path (3F.4b / 3P.3b). Contains intra-module dimensions only — D5, D7, D10-D15 are deferred to the cross-module agent.

```
MODULE_REVIEW_SCOPE:
  group_id: <string — e.g. "src/binding", "serializers">
  primary_files: [<file paths reviewed in full by this agent — same as input>]
  tier2_files: [<subset of input `in_diff_files` that this agent actually opened for depth-1 cross-module expansion; files never touched during chain-building are NOT listed here even if they were in in_diff_files>]

METHOD_CHAINS:
# Scope: public symbols in this module group's PRIMARY files only (tier-2 files' symbols
# are NOT top-level entries — they appear only as inlined steps inside primary-module chains).
# Three-tier inlining per §Call-Graph Discipline:
#   Tier 1 (same-module private helpers)     → full recursive inlining, "  helper →" prefix
#   Tier 2 (cross-module callees in diff)    → depth-1 inlining,        "  X:Module.method →" prefix
#   Tier 3 (stdlib, third-party, not in diff) → ext_call leaf, no expansion
# Test files are exempt.
- symbol: <ClassName.method_name | function_name>
  file: <path — must be one of primary_files>
  line: <number>
  purpose: <one-line purpose>
  chain: [... steps per three-tier inlining convention ...]
  chain_completeness: <matches_purpose | partial | suspicious>
  gaps: [...]
  external_inputs:
  # external_inputs[].via values:
  #   "direct"              — iterate/subscript happens in the public method's own body
  #   "<helper_name>"       — happens inside a tier-1 inlined private helper
  #   "X:<Module.method>"   — happens inside a tier-2 inlined cross-module callee
  - { source: <name>, guarded: <true | false>, guard_detail: "<...>", via: "<direct | helper_name | X:Module.method>" }
  tier2_callees:
  # Every tier-2 cross-module callee inlined in this chain — lets the orchestrator cross-check
  # coverage and deduplicate issues that also get flagged by the agent owning the callee's module.
  - callee: <Module.method>
    callee_file: <path>
    lines_referenced: [<line numbers in callee_file that were inlined>]

METHOD_CHAINS_DEFERRED:
- symbol: <ClassName.method_name>
  file: <path>
  reason: <scope-too-large | unreadable-source | generated-code>

INTRA_MODULE_SUMMARY:
  total_issues: <number>
  blocker_count: <number>
  critical_count: <number>
  warning_count: <number>
  suggestion_count: <number>

FUNCTIONAL_CORRECTNESS:              # D1
  rating: <pass | warning | critical>
  issues:
  - severity: <blocker | critical | warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <problem → why it matters → suggested fix>
    suggestion: <how to fix>
    evidence: <REQUIRED for critical/blocker; for D1 defensive-gap findings MUST include trust-boundary argument per §Finding Suppression Gate Gate 2>

SECURITY:                            # D2
  rating: <pass | warning | critical>
  issues: [same structure — evidence REQUIRED for critical/blocker, MUST include trust-boundary argument]

RESOURCE_MANAGEMENT:                 # D3
  rating: <pass | warning | critical>
  issues: [same structure — evidence REQUIRED for critical/blocker]

CODE_QUALITY:                        # D4
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <critical | warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <problem → why it matters>
    suggestion: <how to fix>
    evidence: <REQUIRED for critical>

PERFORMANCE:                         # D6
  rating: <good | acceptable | needs_work>
  issues: [same structure as D4 — evidence REQUIRED for critical]

ERROR_HANDLING_AND_OBSERVABILITY:    # D8 + D9
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    category: <error_handling | logging | metrics | tracing>
    title: <short title>
    description: <problem → why it matters>
    suggestion: <how to fix>
    evidence: <SHOULD be present for warning when non-obvious; OPTIONAL for suggestion>
```

---

## Cross-Module Sub-agent Format

Used by the single cross-module aggregation agent in the layered review path (3F.5 / 3P.4). Receives all per-module METHOD_CHAINS. Applies cross-cutting dimensions and consistency checks.

```
CROSS_MODULE_SUMMARY:
  modules_analyzed: <number>
  total_cross_issues: <number>
  blocker_count: <number>
  critical_count: <number>
  warning_count: <number>
  suggestion_count: <number>

ARCHITECTURE:                        # D5
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <blocker | critical | warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <problem → why it matters>
    suggestion: <how to fix>
    evidence: <REQUIRED for critical/blocker>

TEST_COVERAGE:                       # D7
  rating: <good | acceptable | needs_work>
  coverage_gaps:
  - severity: <critical | warning | suggestion>
    file: path/to/source.ext
    description: <what scenario is untested>
    evidence: <REQUIRED for critical: which observable behavior is at risk because the path is untested>

SIMPLIFICATION_ANTI_BLOAT:          # D15
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <critical | warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <problem → why it matters>
    suggestion: <how to fix>
    evidence: <REQUIRED for critical: what duplicate / parallel implementation / scope creep is concretely demonstrated, with file references>

MAINTAINABILITY_AND_COMPATIBILITY:   # D10 + D11 + D12 + D13
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    category: <standards | backward_compat | tech_debt | dependencies>
    title: <short title>
    description: <problem → why it matters>
    suggestion: <how to fix>
    evidence: <SHOULD be present for warning when non-obvious; OPTIONAL for suggestion>

CROSS_MODULE_CONSISTENCY:
  # Five checks — one entry each. status: consistent means no issues found for that pattern.
  patterns:
  - pattern: <coerce_guard | traceback_preservation | re_export | error_convention | defensive_depth>
    status: <consistent | inconsistent | not_applicable>
    issues:
    - severity: <critical | warning>
      files: [<file_a>, <file_b>]           # both the module that has the pattern and the one that doesn't
      description: <module A does X; module B has equivalent code path but omits X>
      suggestion: <apply the same pattern in module B at file:line>
      evidence: <REQUIRED for critical: trust-boundary argument (per Gate 2) showing the missing guard in module B is a real bug, not pattern divergence on internal/trusted data>

SECOND_ORDER_REVIEW:
  # Extracted fix patterns from per-module METHOD_CHAINS and findings.
  # Each entry = one fix pattern identified in the diff.
  fix_patterns:
  - pattern_description: <e.g., "coerce non-dict display surface values before key access">
    applied_in_modules: [<group_id_a>]
    missing_in_modules: [<group_id_b>, <group_id_c>]   # empty list = no structural parity violation
    severity: <critical | warning | not_applicable>
    issues:
    - severity: <critical | warning>
      files: [<file where fix is missing>]
      description: <structural parity violation description>
      suggestion: <exact fix to apply>
      evidence: <REQUIRED for critical: concrete reachable trigger showing the missing fix in module B produces observable wrong behavior, AND trust-boundary argument per Gate 2>

# Consistency section — one of the three below based on mode/reference_level:

PLAN_CONSISTENCY:             # Feature mode OR planning-backed project mode
  criteria_met: <X/Y>
  unmet_criteria:
  - <criterion not met>
  scope_issues:
  - <unplanned additions or missing planned features>

CONSISTENCY:                  # Docs-backed project mode
  type: doc_consistency
  rating: <good | acceptable | needs_work>
  criteria_met: <X/Y>
  unmet_criteria:
  - <criterion not met>
  scope_issues:
  - <undocumented features or missing requirements>

# bare project mode: omit consistency section entirely; note "bare — consistency skipped" in CROSS_MODULE_SUMMARY
```
