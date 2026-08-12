# Review Report Template

Display the following report directly in the terminal using markdown.

## Header

```markdown
# {title}
```

- **Feature mode title:** `Code Review: {feature_name}`
- **Project mode title:** `Project Review: {project_name}`

```markdown
**Date:** {ISO date}
**Reviewer:** code-forge
**Overall Rating:** {pass | pass_with_notes | needs_changes}
**Merge Readiness:** {ready | fix_required | rework_required}
```

**Project mode only — add these header fields:**

```markdown
**Scope:** {changes (N changed + M related files) | full (N source files)}
**Reference:** {planning-backed | docs-backed | bare (no reference documents)}
```

## Body

The Acceptance Gate section is rendered FIRST — above Summary — whenever the gate ran (i.e. not `--quick`). It is the merge-blocking verdict; dimensional findings come after it.

```markdown
## Acceptance Gate

**Verdict:** {✅ PASS | 🚫 BLOCKED | ⚠ PASS (unreconciled) | ⏭ skipped (--quick)}
**Source:** {srs `docs/{feature}/srs.md` | test-cases `docs/{feature}/test-cases.md` | plan `plan.md` | docs | none}
**Dynamic verification:** {tests_passed} passed · {tests_failed} failed · {tests_skipped} skipped {| no runnable suite found}
**Coverage:** {covered}/{required_total} P0/P1 required behaviors backed by a passing test

{If BLOCKED — list the gate failures, P0 first. These are merge blockers and appear ABOVE all dimensional findings:}

| Behavior | Priority | Status | Missing test / failing test |
|----------|----------|--------|-----------------------------|
| {id — description} | P0 | uncovered | No test exercises this behavior |
| {id — description} | P0 | weak | {test name} passes but asserts only the happy path; no boundary/error assertion |
| {test name} | — | failing | {one-line failure reason from the run} |

{If P1 gaps exist (non-blocking criticals):}
**P1 gaps (non-blocking, fix recommended):** {id — description}, ...

{If PASS (unreconciled):}
> No authoritative acceptance source (SRS / test-cases / acceptance criteria) found — coverage reconciliation skipped; only dynamic verification ran. Run `/spec-forge:srs` or `/spec-forge:test-cases` to enable reconciliation.

{If skipped:}
> Acceptance Gate skipped (`--quick`) — this was a static-only review. Tests were NOT run and acceptance coverage was NOT verified. Re-run without `--quick` before treating this as merge-ready.

---

## Summary

{1-2 paragraph summary of the review findings}

**Issue Breakdown:** {blocker_count} blockers · {critical_count} critical · {warning_count} warnings · {suggestion_count} suggestions

**Call-Graph Coverage:** {N} public symbols analyzed · {n_partial} partial chains · {n_suspicious} suspicious chains
{If METHOD_CHAINS_DEFERRED non-empty:} ⚠ {N} symbols deferred — not analyzed. Reasons: {comma-separated reasons}

### Report Health

| Metric | Value | Threshold (healthy / advisory / flagged) | Status |
|---|---|---|---|
| Verdict | {verdict_emoji_concatenated} **{verdict}** | — | — |
| Finding density | {finding_density}/100 LOC | ≤ 1.0 / 1.0–2.0 / > 2.0 → noisy | {✅ / ⚠ / 🚨} |
| Critical share | {critical_share_pct}% | ≤ 5% / 5–10% / > 10% → inflated (skipped if total < 10) | {✅ / ⚠ / 🚨 / —} |
| Auto-downgrade share | {auto_downgrade_share_pct}% | ≤ 15% / 15–30% / > 30% → gated (skipped if pre-downgrade top < 3) | {✅ / ⚠ / 🚨 / —} |
| Drop share | {drop_share_pct}% | ≤ 20% / 20–40% / > 40% → fabricating (skipped if raw findings < 10) | {✅ / ⚠ / 🚨 / —} |
| LOC reviewed | {LOC_reviewed} | — | — |
| Top severity (pre-downgrade → post) | {top_pre_downgrade} → {top_post} | — | — |
| Raw → post-drop findings | {raw_findings_count} → {total_issues} | — | — |

Status legend: ✅ healthy band · ⚠ advisory band (no flag raised but worth noting) · 🚨 unhealthy band (flag raised) · — exempted (small report).

{If any Suppression-Gate auto-downgrades occurred:}
**Suppression-Gate downgrades ({n_auto_downgrades} total):** {n_missing_evidence} missing-evidence · {n_trust_boundary} internal-trust-boundary

{If any Suppression-Gate drops occurred:}
**Suppression-Gate drops ({dropped_total} total):** {n_speculative} speculative-phrasing · {n_warning_no_downside} warning-no-observable-downside · {n_warning_unverified_claim} unverified-factual-claim · {n_suggestion_no_benefit} suggestion-no-concrete-benefit · {n_suggestion_nitpick} suggestion-nitpick · {n_suggestion_over_budget} suggestion-over-budget · {n_suggestion_consolidated} suggestion-consolidated

{If verdict != healthy, render one block-quote line per raised flag:}
> ⚠ {flag_name}: {hint per SKILL.md §6.3 Verdict Emoji & Hints}

---

## Tier 1 — Must-Fix Before Merge

### Functional Correctness (D1)

**Rating:** {rating}

{issues table with severity/file/line/title/description/suggestion, or "No issues found"}

### Security (D2)

**Rating:** {rating}

{issues or "No security concerns"}

### Resource Management (D3)

**Rating:** {rating}

{issues or "No resource management issues"}

---

## Tier 2 — Should-Fix

### Code Quality (D4)

**Rating:** {rating}

{issues or "No issues found"}

### Architecture & Design (D5)

**Rating:** {rating}

{issues or "No issues found"}

### Performance (D6)

**Rating:** {rating}

{issues or "No issues found"}

### Test Coverage (D7)

**Rating:** {rating}

{coverage gaps or "All scenarios covered"}

---

## Tier 3 — Recommended

### Error Handling & Observability (D8/D9)

**Rating:** {rating}

{issues or "No issues found"}

---

## Tier 4 — Nice-to-Have

### Maintainability & Compatibility (D10–D13)

**Rating:** {rating}

{issues or "No issues found"}

{If frontend/fullstack:}
### Accessibility / i18n (D14)

**Rating:** {rating}

{issues or "Skipped (not a frontend project)"}
```

## Consistency Section (mode-specific)

- **Feature mode (always):**

```markdown
---

## Plan Consistency

**Criteria Met:** {X/Y}

{unmet criteria or "All criteria met"}
```

- **Project mode (planning-backed):**

```markdown
---

## Plan Consistency

**Criteria Met:** {X/Y}

{unmet criteria or "All criteria met"}
```

- **Project mode (docs-backed):**

```markdown
---

## Documentation Consistency

**Criteria Met:** {X/Y}

{unmet criteria or "All criteria met"}
```

- **Project mode (bare):**

```markdown
*No reference documents found — consistency check skipped.*
```

## Cross-Module Section (layered path only)

Only include this section when the layered review path was used (≥ 3 affected files AND ≥ 2 module groups).

```markdown
---

## Cross-Module Analysis

**Modules Reviewed:** {N} module groups in parallel

### Tier-2 Coverage

{Include this subsection ONLY when at least one module group reported `tier2_budget_exceeded: true`. Omit entirely otherwise — do not print an empty "all within budget" line.}

**Over-budget module groups:** {group_id (eligible: N callee files, expanded: 8), ...}

{When every deferred callee was reconciled by the cross-module agent:}
All {N} deferred cross-module callees were expanded in the cross-module pass. No coverage gap.

{When `n_tier2_unreconciled ≥ 1` — this line is mandatory and goes ABOVE the consistency table:}
> :warning: **Coverage gap.** {N} cross-module callee(s) exceeded the per-module tier-2 expansion budget and were not expanded by any agent: {callee list with file paths}. Defensive gaps on those call boundaries are outside this review's coverage. Re-run with a narrower scope to cover them.

### Cross-Module Consistency

{For each of the five CROSS_MODULE_CONSISTENCY patterns — list status and any issues, or "No issues" if consistent}

| Pattern | Status | Issues |
|---------|--------|--------|
| Coerce/guard pattern | consistent / inconsistent | {count or —} |
| Traceback preservation | consistent / inconsistent | {count or —} |
| Re-export completeness | consistent / inconsistent | {count or —} |
| Error handling convention | consistent / inconsistent | {count or —} |
| Defensive coding depth | consistent / inconsistent | {count or —} |

{List any inconsistency issues with file references and suggested fixes}

### Second-Order Review (D-Series Prevention)

{List each fix pattern found in the diff and whether it was applied uniformly}

{If no structural parity violations:} All fix patterns applied uniformly across modules.

{If violations found:}
- **{pattern_description}** — applied in `{module_a}`, missing in `{module_b}` — `critical`
  > {description of what to fix and where}
```

## Recommendations and Verdict

```markdown
---

## Recommendations

{Prioritized list of changes, grouped by blocking status:}

**Must fix before merge:**
1. {highest priority fix with file:line reference}
2. ...

**Should fix:**
1. {recommended fix}
2. ...

**Consider for later:**
1. {nice-to-have improvement}
2. ...

## Verdict

{Final assessment: merge as-is, fix blockers/criticals then merge, or needs rework}
```
