# Case Study: apcore-cli-typescript (2026-04-22)

Regression baseline for the **pre-emission scratchpad + Drop Gallery**
optimization landed in the `code-forge:review` skill.

**This file is human-reference. Not loaded at runtime. See `README.md`.**

---

## Skill revision at test time

| Component | State |
|---|---|
| `skills/review/SKILL.md` | working-tree commit `66e9a60` + uncommitted scratchpad/gallery changes |
| `skills/review/references/suppression-gates.md` | includes Drop Gallery §: 8 ❌ examples + 2 ✅ examples + enum taxonomy |
| `skills/review/references/sub-agent-format.md` | includes §Pre-emission Scratchpad + `CANDIDATE_INVENTORY` block in all 3 format variants |
| Orchestrator Step 0 | scratchpad audit (0a presence, 0b enum compliance, 0c KEEP↔output-block, 0d DROP↔output-block, 0e reason-shape) |
| Drop enum taxonomy | 14 DROP codes + 7 KEEP codes |

**Target commit for re-run:** pin to the commit that lands these changes (once committed — currently uncommitted).

## Project profile

| Dimension | Value |
|---|---|
| Source files | 24 |
| LOC | 6253 |
| Reference level | planning-backed (10 plans + 1 sub-plan with 10 tasks) |
| Module groups (layered path) | 7 |
| Language / project type | TypeScript / CLI library |
| Trust-model notes | Consumes developer-authored YAML and CLI input; no network / untrusted user input — informs Gate 2 behavior |

---

## Baseline metrics (what to watch on regression)

| Metric | Baseline | Regression threshold | Reason for threshold |
|---|---|---|---|
| **Total findings** | 6 | `4` ≤ x ≤ `10` | < 4 → skill under-detecting; > 10 → noise returning |
| **Blocker count** | 0 | = 0 | No known blocker-class bug in scope |
| **Critical count** | 3 | = 3 | Three real cross-dispatcher defects; any fewer → skill missed them |
| **Warning count** | 3 | 1 ≤ x ≤ 5 | < 1 → under-detecting legitimate D7/D8/D10 warnings; > 5 → severity inflation |
| **Suggestion count** | 0 | ≤ 2 | > 2 → nitpick filter / Drop Gallery regressed |
| **Finding density** | 0.10/100 LOC | ≤ 0.30 | > 0.30 → general noise regression |
| **Critical share** | 50% (small-report exempt) | true positives expected | Exempted by `total < 10` rule — manually re-verify each critical is reachable |
| **Orchestrator drops** (`dropped_total`) | 0 | ≤ 3 | > 3 means Gates 1–7 are doing work the scratchpad should have done — scratchpad degraded |
| **Sub-agent success rate** | 7/7 module groups | ≥ 7/7 | < 7 → usage-limit regression returned |
| **`n_scratchpad_bypass`** | 0 | = 0 | Any bypass attempt → auto `fabricating` flag by design |
| **`n_orphan_finding`** | 0 | ≤ 1 | > 1 → sub-agents emitting without inventorying |

---

## Capability contract (must detect)

The skill MUST surface, at `critical` severity:

1. **Cross-dispatcher policy-gate parity defect** — a canonical dispatch path
   applies a set of gates (approval / audit / sandbox) that a parallel,
   user-reachable dispatch path skips. Evidence requires citing both paths
   with file:line AND a concrete trigger showing observable asymmetry
   (e.g. exit code same, audit trail empty on one path).

2. **Second occurrence of the same defect class in a sibling method** — once
   the SECOND_ORDER_REVIEW fix-pattern extraction identifies the canonical
   gate set, it must check every sibling dispatcher, not just the first one.
   Detecting only the first instance = partial credit; missing the sibling
   = `cross_module_drift_observable` enum code not being used effectively.

3. **Dispatcher-table parameter drop** — an optional parameter constructed at
   setup time, stashed on a program object, but never forwarded through the
   dispatcher's registration table — rendering an advertised CLI flag inert.
   Evidence requires grepping for read sites of the stashed value and showing
   zero consumers.

## Suppression contract (must drop — abstract shapes)

The skill MUST NOT surface (these are the scratchpad's job to drop at
candidate time, with matching `decision_reason` enum):

| Abstract noise shape | Expected enum code |
|---|---|
| Extract-helper proposal where duplication spans only 2 sites | `extract_helper_under_3_sites` |
| Refactor introducing a new typed wrapper (interface / helper) to replace casts that have not produced an observed bug | `refactor_preference_no_bug` |
| Divergence-from-upstream item that the project's own CLAUDE.md / TODOs already track | `documented_known_gap` |
| Suggestion whose own description contains *"impact is small"* / *"only worth if X surfaces"* | `self_admitted_low_value` |
| "Sibling module A does X, module B does Y" without a named caller consequence | `pure_symmetry_no_bug` |
| Runtime type-check proposal against a developer-controlled input (schema authored by the tool's own user) | `defensive_hardening_speculative` |
| Speculative surrogate-pair / emoji edge-case hardening in output formatting | `self_admitted_low_value` or `defensive_hardening_speculative` |
| Hypothetical future typo ("a typo WOULD no-op if someone ever introduces one") | `typo_hypothetical` |

If any of these shapes appear as emitted findings (not just as DROP rows in
`CANDIDATE_INVENTORY`), the Drop Gallery has regressed — investigate recent
edits to `references/suppression-gates.md` §Drop Gallery and
`references/sub-agent-format.md` §Pre-emission Scratchpad.

## Pre-optimization anti-baseline

Before the scratchpad + gallery landed, the same project returned **18
findings** on the same skill (0 blocker, 0 critical, 9 warning, 9 suggestion)
with orchestrator drops = 2. Of the 9 suggestions, approximately 6 were noise
matching the shapes listed above. The pre-optimization run also:

- Missed 2 of the 3 real critical bugs (found only the first cross-dispatcher
  defect, missed the sibling; missed the inert-flag defect entirely).
- Classified the one critical bug it did find as `warning` rather than
  `critical`.
- Had 3 of 6 per-module sub-agents fail with usage-limit (no retries,
  degraded fallback).

A future run should not regress toward that shape. Watch for:
- suggestion count rising back above 3
- critical count dropping to 0 or 1 (under-detection)
- orchestrator drops rising above 3 (scratchpad not doing its job)
- any module group showing usage-limit failure

---

## How to re-run

```bash
# 1. Check out skill at baseline commit (once committed)
cd /Users/tercel/WorkSpace/skills/code-forge
git checkout <baseline-commit-sha>

# 2. Run review against the same project
cd ../../aipartnerup/apcore-cli-typescript
/code-forge:review --project
```

Compare the resulting metric table header against the baseline above. If any
row crosses its threshold band, the skill regressed — diff `skills/review/`
between the working commit and the baseline commit to find the cause.

## Known exemptions active in this baseline

- **Critical share 50%** is flagged as "advisory-to-unhealthy" by the normal
  formula but suppressed by the `total_issues < 10` small-report exemption.
  All 3 criticals here are true positives, so the exemption is correct
  behavior. If a future baseline has small-report `critical share > 50%` and
  any of the criticals is a false positive, the exemption rule itself needs
  review (not this baseline).
