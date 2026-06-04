# Sub-agent Response Format

The review sub-agent must return results in the following structured YAML format.

**Note:** Feature mode and Project mode have slightly different fields in `REVIEW_SUMMARY` and the final consistency section. See the mode-specific notes below.

**`METHOD_CHAINS` is MANDATORY and comes first — the orchestrator rejects any response without it.** See the `references/call-graph-discipline.md` (full protocol including anti-rationalization guard) for the protocol. The sub-agent must produce one `METHOD_CHAINS` entry per public method / exported function / entry-point in the reviewed scope, then apply dimensions against the graph, not against surface method bodies.

**`CANDIDATE_INVENTORY` is MANDATORY and comes BETWEEN `METHOD_CHAINS` and the dimension blocks.** This is the pre-emission scratchpad: every candidate finding discovered during dimension application must appear here with an explicit `KEEP` or `DROP` decision and a fixed-enum `decision_reason` code. This enforces the Anthropic pre-emission-CoT pattern — the sub-agent makes the keep/drop judgment *before* writing the dimension blocks, not as a post-hoc filter. See `references/suppression-gates.md` §Drop Gallery for the concrete examples each DROP code corresponds to, and see §Pre-emission Scratchpad below for the full schema.

**`evidence` field is MANDATORY for every `critical` and `blocker` finding.** See `references/suppression-gates.md`. The orchestrator rejects critical/blocker findings missing `evidence` and (after one re-invoke) auto-downgrades them with a `[Auto-downgraded: missing evidence]` marker. `evidence` SHOULD be present for `warning` findings when non-obvious; OPTIONAL for `suggestion`. The field must show: (a) the concrete input/condition that triggers the failure, (b) the observable wrong behavior, and (c) for D2 / D1-defensive-gap findings, the trust-boundary argument per Gate 2.

**`evidence` is ALSO MANDATORY at any severity (including `warning` and `suggestion`) when the finding makes a falsifiable factual claim about the codebase** — Gate 5 in `references/suppression-gates.md`. Trigger phrases: `zero references`, `zero reads`, `never called`, `never read`, `dead code`, `unreachable`, `unused`, `only used in`, `only referenced in`, `sole consumer`, `duplicates X`, `copy of`, `redeclares`, `parallel implementation`, `reimplements`, `grep (returns|shows|finds)`, `N lines exceed`, `exceeds N lines`. When any of these appear in `title` / `description`, `evidence` MUST include:

- **Option A — command + output:** The full `grep` / `rg` / search command that was actually run, AND one or more lines of its matched output (in `path:line:content` format), OR the explicit string `0 matches` / `no matches` when claiming absence. A single-sentence summary (*"grep returns only the declaration"*) is NOT sufficient — the raw output itself must be visible.
- **Option B — file:line citations:** Explicit `path/to/file.ext:LINE` references covering every site the claim depends on. A "duplicates Y" claim must cite both the original and the duplicate. An "only used in foo.ts" claim must cite foo.ts AND carry a grep proving no other uses. A "dead code" claim requires cross-directory coverage (src + tests at minimum).

Example (warning-level factual claim) — **acceptable**:
```yaml
evidence: |
  grep -rn "ERROR_CODE_MAP" src/ tests/
  src/main.ts:111:const ERROR_CODE_MAP: Record<string, number> = {
  src/main.ts:1129:    const exitCode = errorCode && errorCode in ERROR_CODE_MAP
  src/main.ts:1130:      ? ERROR_CODE_MAP[errorCode]
  → 2 read sites in same file as declaration; overlaps with errors.ts:135 codeMap
    (which has these entries too: MODULE_NOT_FOUND, SCHEMA_VALIDATION_ERROR, APPROVAL_DENIED).
  Proposed: consolidate readers to codeMap, delete main.ts:111-134.
```

Example (warning-level factual claim) — **rejected by Gate 5**:
```yaml
evidence: "grep returns only the declaration; zero reads."
```
The second example is rejected because the grep *output* is not visible — only a paraphrase. The sub-agent may have mis-read the output or greppped too narrow a scope; without the actual matched lines in evidence, the orchestrator cannot distinguish a true zero-reference claim from a false one.

---

## Pre-emission Scratchpad (`CANDIDATE_INVENTORY`)

Every candidate finding discovered while applying dimensions MUST appear in `CANDIDATE_INVENTORY` with an explicit `KEEP` or `DROP` decision BEFORE it appears (or doesn't) in a dimension block. This is the Anthropic pre-emission-CoT pattern: force the keep/drop decision with justification up front, rather than writing all findings into dimension blocks and hoping a post-hoc gate catches the noise.

**Rules:**
1. Every candidate — whether you intend to KEEP or DROP it — must have a row in `CANDIDATE_INVENTORY`.
2. `decision_reason` MUST be one of the fixed enum values below. Free-text reasons are rejected by the orchestrator (see SKILL.md Step 4F/4P scratchpad audit).
3. For every KEEP candidate, exactly one dimension block must contain a matching issue (same `file:line` + `title`). Orchestrator cross-checks.
4. For every DROP candidate, NO dimension block may contain a matching issue. Orchestrator cross-checks — attempting to DROP in the scratchpad but KEEP in dimensions is flagged as a bypass attempt and the finding is rejected outright.
5. If dimensions were truly empty, the inventory may be empty — but empty inventory + any finding in dimension blocks is rejected.

**KEEP reason codes (enum):**

| Code | When to use |
|---|---|
| `concrete_bug_reachable` | Concrete input triggers observable wrong behavior (D1/D3/D6/D8). |
| `cross_module_drift_observable` | Sibling modules with symmetric contract diverge in observable behavior — e.g. module A has guard/audit/approval, module B does not; module A coerces input, module B does not. Requires contract-symmetry pre-flight (see §CROSS_MODULE_CONSISTENCY). |
| `factual_claim_verified_with_grep` | "Zero references" / "dead code" / "duplicates" claim with actual `grep`/`rg` command + output in `evidence`. |
| `consolidation_3plus_sites_verified` | ≥3 sites of real duplication verified with grep output; extraction target exists or benefit is named concretely. |
| `critical_path_untested` | D7 — a path with observable failure mode has no test coverage (requires naming the failure mode). |
| `plan_criterion_unmet` | An acceptance criterion from `plan.md` is not met in the code. |

**DROP reason codes (enum):**

| Code | Canonical trigger |
|---|---|
| `extract_helper_under_3_sites` | Duplicate appears in only 2 sites. |
| `refactor_preference_no_bug` | Fix introduces a new abstraction replacing a working pattern; no observed bug. |
| `documented_known_gap` | Description self-identifies as already-tracked (CLAUDE.md, TODO, next release). |
| `self_admitted_low_value` | "impact is small", "only worth if X surfaces", "edge case", "theoretical concern". |
| `pure_symmetry_no_bug` | "Inconsistent with sibling" with no named caller consequence. |
| `rename_for_clarity_no_ambiguity` | Rename without concrete past-confusion incident or mis-describing name. |
| `speculative_phrasing` | Description contains "could theoretically", "if X ever", "in case someone", "potentially might". |
| `trust_boundary_internal` | D1/D2 finding on developer-authored / type-checked / internal input source. |
| `unverified_factual_claim` | Gate 5 trigger phrase ("zero references", "dead code", "only used in") without grep output or file:line evidence. |
| `defensive_hardening_speculative` | Runtime check against an input source that is developer-controlled. |
| `typo_hypothetical` | "A typo WOULD no-op" — the typo doesn't exist in the code. |
| `packaging_naming_out_of_scope` | Binary-name collision / npm-scope / bin-script rename when review scope doesn't include packaging. |
| `style_swap_no_downside` | "Prefer X over Y" / "consider using X instead" without a named downside of Y. |
| `formatting_casing_linter_territory` | Whitespace, camelCase vs snake_case, `WARNING:` vs `Warning:` — linter concern, not review. |

**Scratchpad schema:**

```
CANDIDATE_INVENTORY:
- id: C1
  dimension: <D1 | D2 | D3 | ... | D15>
  file: path/to/file.ext
  line: <number or range>
  title: <short title — must match the title in the dimension block if decision=KEEP>
  decision: <KEEP | DROP>
  decision_reason: <one of the enum codes above — NO free text>
  decision_detail: <one line — why THIS code applies to THIS candidate, e.g.
                   "2 sites (main.ts:937 and :982), below 3-site threshold">
- id: C2
  ...
```

**Example inventory (hypothetical review with 6 candidates):**

```
CANDIDATE_INVENTORY:
- id: C1
  dimension: D1
  file: src/discovery.ts
  line: 289
  title: "apcli exec bypasses checkApproval and audit-log writes"
  decision: KEEP
  decision_reason: cross_module_drift_observable
  decision_detail: "discovery.ts:289 invokes executor.execute directly; main.ts:1038 wires approval+audit for buildModuleCommand with symmetric contract"
- id: C2
  dimension: D4
  file: src/main.ts
  line: 937
  title: "reserved-set redeclared at two sites"
  decision: DROP
  decision_reason: extract_helper_under_3_sites
  decision_detail: "appears at main.ts:937 and main.ts:982 — 2 sites, below 3-site threshold"
- id: C3
  dimension: D4
  file: src/cli.ts
  line: 17
  title: "Local Registry placeholders diverge from upstream apcore-js"
  decision: DROP
  decision_reason: documented_known_gap
  decision_detail: "description itself references CLAUDE.md tracking and next apcore-js compatibility bump"
- id: C4
  dimension: D4
  file: src/output.ts
  line: 39
  title: "truncate slices on UTF-16 code units"
  decision: DROP
  decision_reason: self_admitted_low_value
  decision_detail: "suggestion text includes 'behavioral impact is small; only worth doing if broken-glyph reports surface'"
- id: C5
  dimension: D4
  file: src/main.ts
  line: 403
  title: "_exposureFilter attached via as unknown as Record cast"
  decision: DROP
  decision_reason: refactor_preference_no_bug
  decision_detail: "fix introduces ProgramMeta interface; no observed typo or runtime bug — 'a typo WOULD no-op' is hypothetical"
- id: C6
  dimension: D15
  file: src/system-cmd.ts
  line: 207
  title: "emitResult helper re-implemented in 5 registrars"
  decision: KEEP
  decision_reason: consolidation_3plus_sites_verified
  decision_detail: "grep -n 'fmt === \"json\"' yields 5 inline sites + 1 helper; concrete maintenance cost named"
```

In the above, only C1 and C6 appear in dimension blocks. C2–C5 never leave the scratchpad. The orchestrator audits both directions: KEEP candidates must appear in dimensions, DROP candidates must not.

---

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
# MANDATORY — every candidate finding with KEEP/DROP decision and fixed-enum reason.
# See §Pre-emission Scratchpad above for the full enum taxonomy.
# Orchestrator cross-checks: KEEP → must appear in dimension blocks; DROP → must NOT appear.
- id: <C1 | C2 | ...>
  dimension: <D1 | D2 | ... | D15>
  file: path/to/file.ext
  line: <number or range>
  title: <short title>
  decision: <KEEP | DROP>
  decision_reason: <enum code from §Pre-emission Scratchpad — NO free text>
  decision_detail: <one line — why this code applies to this candidate>

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
# Three-tier inlining per `call-graph-discipline.md`:
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

CANDIDATE_INVENTORY:
# MANDATORY — every intra-module candidate finding with KEEP/DROP decision and fixed-enum reason.
# Scope: D1, D2, D3, D4, D6, D8, D9 findings rooted in THIS module's METHOD_CHAINS,
# including findings discovered via tier-2 inlined cross-module steps.
# See §Pre-emission Scratchpad for the full enum taxonomy.
- id: <C1 | C2 | ...>
  dimension: <D1 | D2 | D3 | D4 | D6 | D8 | D9>
  file: path/to/file.ext
  line: <number or range>
  title: <short title>
  decision: <KEEP | DROP>
  decision_reason: <enum code — NO free text>
  decision_detail: <one line — why this code applies>

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
CANDIDATE_INVENTORY:
# MANDATORY — every cross-module candidate finding with KEEP/DROP decision and fixed-enum reason.
# Scope: D5, D7, D10-D15, CROSS_MODULE_CONSISTENCY, SECOND_ORDER_REVIEW.
# See §Pre-emission Scratchpad for the full enum taxonomy.
- id: <C1 | C2 | ...>
  dimension: <D5 | D7 | D10 | D11 | D12 | D13 | D15 | cross_module_consistency | second_order_review>
  file: path/to/file.ext
  line: <number or range>
  title: <short title>
  decision: <KEEP | DROP>
  decision_reason: <enum code — NO free text>
  decision_detail: <one line — why this code applies>

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
    evidence: <MANDATORY AT ANY SEVERITY for D15 — every D15 finding asserts a Gate 5 factual claim (dead code, duplicate, parallel implementation, scope creep, unused, only-used-in-X). Evidence MUST paste the actual `grep -rn` / `rg` command AND its matched-line output covering at least `src/` + `tests/` for dead-code claims, OR cite both sides with file:line for duplicate / parallel claims. A narrative summary like "grep returns only the declaration" is insufficient — orchestrator Step 4F validation #4b drops D15 findings lacking the command+output or file:line citations.>

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

---

## Acceptance Reconciliation Sub-agent Format

Used by the dedicated acceptance sub-agent in **Step 3G.3** (the Acceptance Gate). This agent has the OPPOSITE polarity from the correctness-review agents: its job is to report ABSENCE of test coverage for required behaviors, not to find bugs in code that exists.

**This agent does NOT produce `METHOD_CHAINS` and does NOT produce `CANDIDATE_INVENTORY`. Its findings do NOT pass through the five Suppression Gates, the Gate-5 evidence-artifact requirement, the speculative-phrase scan, or the observable-downside check.** An uncovered required behavior is the finding; absence is the evidence. Never drop or downgrade an acceptance gap for lack of a reachable-trigger argument or grep artifact.

**Input the agent receives:** `REQUIRED_BEHAVIORS` (the P0/P1 items resolved in Step 3G.1), the list of test files, and the executed-test names + pass/fail status from the fresh run in Step 3G.2.

**Mapping rule:** a behavior is `covered` ONLY when a test (a) exists, (b) executed in this run, (c) passed, and (d) demonstrably exercises the behavior — matched by TC-ID embedded in the test name, or by behavior/assertion when no TC-ID convention exists. Happy-path-only assertions for a behavior that requires boundary/error/negative checks ⇒ `weak`. Skipped / todo / pending / `to-be-automated` ⇒ never `covered`.

```
ACCEPTANCE_RECONCILIATION:
  source: <srs | test-cases | plan | docs | none>
  required_total: <number of P0/P1 behaviors>     # 0 when source == none
  covered: <number>
  uncovered_p0: <number>
  uncovered_p1: <number>
  behaviors:
  - id: <FR-AUTH-001 | TC-AUTH-010 | AC-3 | ...>
    priority: <P0 | P1>
    description: <one line — the required behavior / expected result>
    status: <covered | uncovered | weak>
    test: <test name + file:line that covers it>     # required when status == covered
    note: <for weak: which sub-aspect (boundary/error/negative) is unasserted; for uncovered: omit — absence needs no further evidence>
```

**Verdict computation is done by the orchestrator (Step 3G.4), not the sub-agent.** The orchestrator converts every `uncovered`/`weak` P0 → blocker, every `uncovered`/`weak` P1 → critical, merges these counts into the report, and sets `ACCEPTANCE_GATE = BLOCKED` accordingly.
