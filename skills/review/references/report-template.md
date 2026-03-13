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

```markdown
## Summary

{1-2 paragraph summary of the review findings}

**Issue Breakdown:** {blocker_count} blockers · {critical_count} critical · {warning_count} warnings · {suggestion_count} suggestions

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
