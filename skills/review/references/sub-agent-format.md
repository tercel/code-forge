# Sub-agent Response Format

The review sub-agent must return results in the following structured YAML format.

**Note:** Feature mode and Project mode have slightly different fields in `REVIEW_SUMMARY` and the final consistency section. See the mode-specific notes below.

**`METHOD_CHAINS` is MANDATORY and comes first — the orchestrator rejects any response without it.** See the §Call-Graph Discipline section of the parent SKILL.md for the protocol. The sub-agent must produce one `METHOD_CHAINS` entry per public method / exported function / entry-point in the reviewed scope, then apply dimensions against the graph, not against surface method bodies.

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
    #   call: <helper_name>           — function/method invocation; when the helper is a private same-scope
    #                                    helper, IMMEDIATELY follow with its inlined steps (indented detail +
    #                                    "helper_name →" prefix). Do NOT leave a same-scope private call as
    #                                    a bare step without inlined body.
    #   ext_call: <lib.func>          — LEAF — stdlib, third-party library, framework, OR private helper
    #                                    defined in a DIFFERENT file not in the reviewed set. Only form that
    #                                    is not expanded.
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
    # INLINING CONVENTION (mandatory for same-scope private helpers):
    # Follow the `call` step with the helper's body, each step's `detail` prefixed by two spaces + the
    # helper name + " → ". Two-level: "    HELPER_A → HELPER_B → step". Example:
    #
    #     - { kind: call,      detail: "_discover_custom(rootPaths)",                                   line: 257 }
    #     - { kind: call,      detail: "  _discover_custom → custom_discoverer.discover(roots)",        line: 262 }
    #     - { kind: iterate,   detail: "  _discover_custom → for entry in custom_modules",              line: 263 }
    #     - { kind: subscript, detail: "  _discover_custom → entry['module_id'] (unguarded)",           line: 269 }
    #     - { kind: raise,     detail: "  _discover_custom → KeyError uncaught, aborts whole loop",     line: 269 }
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
  # Every iterate / subscript / deserialize step from `chain` — INCLUDING steps inlined from private helpers.
  # A public method's body can look clean while its chain's `external_inputs` is non-empty because of an
  # unguarded subscript/iterate inside a private helper. This is expected and exactly the bug-class the
  # discipline catches.
  - { source: <name>, guarded: <true | false>, guard_detail: "<null-check | try/except | type guard | schema | none>", via: "<direct | helper_name>" }

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

SECURITY:                                            # D2
  rating: <pass | warning | critical>
  issues: [same structure as D1]

RESOURCE_MANAGEMENT:                                 # D3
  rating: <pass | warning | critical>
  issues: [same structure as D1]

CODE_QUALITY:                                        # D4
  rating: <good | acceptable | needs_work>
  issues:
  - severity: <critical | warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <what's wrong and why it matters>
    suggestion: <how to fix>

ARCHITECTURE:                                        # D5
  rating: <good | acceptable | needs_work>
  issues: [same structure as D4]

PERFORMANCE:                                         # D6
  rating: <good | acceptable | needs_work>
  issues: [same structure as D4]

TEST_COVERAGE:                                       # D7
  rating: <good | acceptable | needs_work>
  coverage_gaps:
  - severity: <critical | warning | suggestion>
    file: path/to/source.ext
    description: <what scenario is untested>

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

ACCESSIBILITY:                                       # D14 (frontend/fullstack only)
  rating: <good | acceptable | needs_work | skipped>
  issues:
  - severity: <warning | suggestion>
    file: path/to/file.ext
    line: <number or range>
    title: <short title>
    description: <what's wrong and why it matters>
    suggestion: <how to fix>
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
