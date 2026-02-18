---
name: review
description: Review code quality for a completed feature — checks code, tests, security, and plan consistency.
---

# Code Forge — Review

Review the code quality of a feature's implementation against its plan, checking code quality, test coverage, security, and consistency.

## When to Use

- Feature implementation is complete or nearly complete
- Want to verify code quality before creating a PR
- Need a structured review against the original plan

## Workflow

```
Locate Feature → Collect Changes → Multi-Dimension Review (sub-agent) → Display Report → Update State → Summary
```

## Context Management

The review analysis is offloaded to a sub-agent to handle large diffs without exhausting the main context.

## Detailed Steps

@../shared/configuration.md

---

### Step 1: Locate Feature

#### 1.1 With Feature Name Argument

If the user provided a feature name (e.g., `/code-forge:review user-auth`):

1. Look for `{output_dir}/{feature_name}/state.json`
2. If not found: show error, list available features

#### 1.2 Without Argument

If no feature name:

1. Scan `{output_dir}/*/state.json` for all features
2. Filter to features with at least one `"completed"` task
3. If none: "No features with completed tasks to review."
4. If one: use it automatically
5. If multiple: use `AskUserQuestion` to let user select

#### 1.3 Load Feature Context

1. Read `state.json`
2. Read `plan.md` (for acceptance criteria and architecture)
3. Note completed task count and overall progress

---

### Step 2: Collect Change Scope

#### 2.1 From Commits

Extract all commit hashes from `state.json` → `tasks[].commits`:
- Flatten all commit arrays into a single list
- If commits are recorded, use `git diff` between the earliest and latest commits
- If no commits recorded, fall back to scanning files involved in tasks

#### 2.2 From Task Files

Read all `tasks/*.md` files and collect their "Files Involved" sections:
- Build a complete list of files created/modified by this feature
- Read current state of each file

#### 2.3 Summary

Store:
- Total files changed
- Total lines added/removed (from git diff)
- List of all affected files

---

### Step 3: Multi-Dimension Review (via Sub-agent)

**Offload to sub-agent** to handle the full diff analysis.

Spawn a `Task` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Review feature: {feature_name}"`

**Sub-agent prompt must include:**
- Feature name and `plan.md` file path
- List of all affected files (sub-agent reads them)
- The acceptance criteria from `plan.md`
- Instructions to review across all dimensions below

**Review dimensions:**

#### 3.1 Code Quality
- Naming conventions: consistent, descriptive, follows project style
- Code structure: appropriate abstractions, no unnecessary complexity
- DRY: no duplicated logic
- Error handling: appropriate error handling at boundaries
- Comments: only where logic isn't self-evident

#### 3.2 Test Coverage
- Every task has corresponding tests
- Tests cover happy path, edge cases, and error cases
- Tests are independent and deterministic
- Test names describe the behavior being tested

#### 3.3 Security
- OWASP top 10 check: SQL injection, XSS, CSRF, etc.
- No hardcoded secrets or credentials
- Input validation at system boundaries
- Proper authentication/authorization checks

#### 3.4 Plan Consistency
- All acceptance criteria from `plan.md` are met
- Architecture matches the design in `plan.md`
- No unplanned features added (scope creep)
- All planned tasks are implemented

**Sub-agent must return:**

    REVIEW_SUMMARY:
      overall_rating: <pass | pass_with_notes | needs_changes>
      total_issues: <number>

    CODE_QUALITY:
      rating: <good | acceptable | needs_work>
      issues:
      - severity: <critical | warning | suggestion>
        file: path/to/file.ext
        line: <number or range>
        description: <what's wrong>
        suggestion: <how to fix>

    TEST_COVERAGE:
      rating: <good | acceptable | needs_work>
      coverage_gaps:
      - <description of untested scenario>

    SECURITY:
      rating: <pass | warning | critical>
      issues:
      - <description of security concern>

    PLAN_CONSISTENCY:
      criteria_met: <X/Y>
      unmet_criteria:
      - <criterion not met>
      scope_issues:
      - <unplanned additions or missing planned features>

---

### Step 4: Display Review Report

Review results are **displayed in the terminal** by default — no file is written. This reflects that reviews are iterative, intermediate checks rather than permanent artifacts.

Display the following report directly in the terminal using markdown:

```markdown
# Code Review: {feature_name}

**Date:** {ISO date}
**Reviewer:** code-forge
**Overall Rating:** {pass | pass_with_notes | needs_changes}

## Summary

{1-2 paragraph summary of the review findings}

## Code Quality

**Rating:** {rating}

{issues table or "No issues found"}

## Test Coverage

**Rating:** {rating}

{coverage gaps or "All scenarios covered"}

## Security

**Rating:** {rating}

{security issues or "No security concerns"}

## Plan Consistency

**Criteria Met:** {X/Y}

{unmet criteria or "All criteria met"}

## Recommendations

{prioritized list of changes to make}

## Verdict

{final assessment and recommendation: merge, fix then merge, or rework}
```

#### 4.1 Optional: Save to File (`--save`)

If the user passed `--save` in the arguments, **also** write the report to `{output_dir}/{feature_name}/review.md`. Otherwise, do NOT create the file.

---

### Step 5: Update state.json

1. Read `state.json`
2. Add or update `review` field in metadata:
   ```json
   {
     "review": {
       "date": "ISO timestamp",
       "rating": "pass_with_notes",
       "total_issues": 3
     }
   }
   ```
   - If `--save` was used, also include `"report": "review.md"` in the review object
3. Update `state.json` `updated` timestamp

---

### Step 6: Summary and Next Steps

Display:

```
Code Review Complete: {feature_name}

Rating: {overall_rating}
Issues: {total_issues} ({critical} critical, {warning} warnings, {suggestion} suggestions)
{If --save was used:}
Report saved: {output_dir}/{feature_name}/review.md

{If needs_changes:}
Recommended actions:
  1. {highest priority fix}
  2. {next priority fix}
  ...
  After fixing: /code-forge:review {feature_name}   Re-run review

{If pass or pass_with_notes:}
Ready for next steps:
  /code-forge:status {feature_name}         View final status
  Create a Pull Request

Tip: use --save to persist the review report to disk
```
