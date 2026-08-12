# Sub-agent Response Format — Per-Module Agent

**Read `format-common.md` first** — it defines the `evidence` requirements and the `CANDIDATE_INVENTORY` drop ledger used below. Dimension check items: `dimensions-intra.md`.

Used by each parallel per-module agent in the layered review path (3F.4b / 3P.3b). Contains intra-module dimensions only — D5, D7, D10-D15 are deferred to the cross-module agent.

```
MODULE_REVIEW_SCOPE:
  group_id: <string — e.g. "src/binding", "serializers">
  primary_files: [<file paths reviewed in full by this agent — same as input>]
  tier2_files: [<subset of input `in_diff_files` that this agent actually opened for depth-1 cross-module expansion; files never touched during chain-building are NOT listed here even if they were in in_diff_files. MAX 8 — the tier-2 expansion budget>]
  tier2_eligible_count: <number of DISTINCT in_diff_files your primary files actually call into, before the budget was applied>
  tier2_budget_exceeded: <true | false>   # true when tier2_eligible_count > 8

METHOD_CHAINS:
# Scope: public symbols in this module group's PRIMARY files only (tier-2 files' symbols
# are NOT top-level entries — they appear only as inlined steps inside primary-module chains).
# Three-tier inlining per `call-graph-discipline.md`:
#   Tier 1 (same-module private helpers)     → full recursive inlining, "  helper →" prefix
#   Tier 2 (cross-module callees in diff)    → depth-1 inlining,        "  X:Module.method →" prefix
#                                              CAPPED at 8 distinct files — see §Tier-2 expansion budget.
#                                              Over budget → mark the step "[tier-2 DEFERRED: over expansion budget]"
#                                              and record it in TIER2_DEFERRED below.
#   Tier 3 (stdlib, third-party, not in diff) → ext_call leaf, no expansion
# Test files are exempt. Tier 1 has NO cap.
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

TIER2_DEFERRED:
# MANDATORY when tier2_budget_exceeded is true; omit the entries (keep the header) otherwise.
# One entry per in-diff cross-module callee you did NOT expand because the budget was spent.
# The orchestrator forwards these to the cross-module agent — an unlisted deferral is
# indistinguishable from a tier-3 leaf and becomes a permanent blind spot. List every one.
- callee: <Module.method>
  callee_file: <path — must be in in_diff_files>
  call_sites:
  - { file: <one of primary_files>, line: <number>, from_symbol: <the public symbol whose chain hit it> }
  call_site_count: <number — this is what the budget ranking was based on>
  reaches_external_input: <true | false | unknown>   # true if the calling chain carries genuinely external data

CANDIDATE_INVENTORY:
# MANDATORY section header — this is a DROP LEDGER.
# List ONLY candidates you considered and decided NOT to emit.
# Scope: D1, D2, D3, D4, D6, D8, D9 candidates rooted in THIS module's METHOD_CHAINS,
#        including ones discovered via tier-2 inlined cross-module steps.
# Findings you KEEP are NOT listed here — they appear in full in the dimension blocks.
# See §Pre-emission Scratchpad in `format-common.md` for the drop-code enum.
# An empty list is valid (nothing was dropped); the header itself is still required.
- id: <C1 | C2 | ...>
  dimension: <D1 | D2 | D3 | D4 | D6 | D8 | D9>
  file: path/to/file.ext
  line: <number or range>
  title: <short title>
  drop_reason: <enum code — NO free text>
  drop_detail: <one line — why this code applies to this candidate>

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
