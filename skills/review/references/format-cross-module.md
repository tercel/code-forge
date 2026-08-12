# Sub-agent Response Format — Cross-Module Agent

**Read `format-common.md` first** — it defines the `evidence` requirements and the `CANDIDATE_INVENTORY` drop ledger used below. Dimension check items: `dimensions-cross.md`.

Used by the single cross-module aggregation agent in the layered review path (3F.5 / 3P.4). Receives all per-module METHOD_CHAINS **plus the merged `TIER2_DEFERRED` list** — the cross-module callees that per-module agents could not expand within their tier-2 budget. Applies cross-cutting dimensions and consistency checks.

**You own the deferred boundaries.** A per-module agent that ran out of tier-2 budget did not drop those callees — it handed them to you, because an unexpanded cross-module boundary is a cross-module concern by definition. Work `TIER2_RECONCILIATION` (below) before the dimension blocks: for each deferred callee you have the global view the per-module agent lacked, and you can open the callee's file directly. Prioritize entries with `reaches_external_input: true` — those are where a defensive gap actually reaches a caller.

```
CANDIDATE_INVENTORY:
# MANDATORY section header — this is a DROP LEDGER.
# List ONLY candidates you considered and decided NOT to emit.
# Scope: D5, D7, D10-D15, CROSS_MODULE_CONSISTENCY, SECOND_ORDER_REVIEW.
# Findings you KEEP are NOT listed here — they appear in full in the dimension blocks.
# See §Pre-emission Scratchpad in `format-common.md` for the drop-code enum.
# An empty list is valid (nothing was dropped); the header itself is still required.
- id: <C1 | C2 | ...>
  dimension: <D5 | D7 | D10 | D11 | D12 | D13 | D15 | cross_module_consistency | second_order_review>
  file: path/to/file.ext
  line: <number or range>
  title: <short title>
  drop_reason: <enum code — NO free text>
  drop_detail: <one line — why this code applies to this candidate>

TIER2_RECONCILIATION:
# MANDATORY when the orchestrator handed you a non-empty merged TIER2_DEFERRED list.
# One entry per deferred callee. Absence of an entry for a handed-over callee is a
# coverage hole — the orchestrator surfaces it as an explicit caveat in the report.
- callee: <Module.method>
  callee_file: <path>
  status: <expanded | expanded_no_issue | not_expanded>
  # expanded          → you opened it and a finding follows in a dimension block below
  # expanded_no_issue → you opened it, chain is clean, no finding
  # not_expanded      → you could not open it; REQUIRES `reason`
  reason: <only when status == not_expanded — e.g. unreadable-source, generated-code>
  finding_ref: <title of the dimension-block issue this produced — only when status == expanded>

CROSS_MODULE_SUMMARY:
  modules_analyzed: <number>
  tier2_deferred_received: <number of callees handed over by per-module agents>
  tier2_deferred_expanded: <number you actually opened>
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
