# Reference Docs Auto-Discovery Design

## Problem

When running `/code-forge:plan`, the plan sub-agent has no awareness of the project's existing architecture, conventions, or specifications. Users must manually reference these in feature documents. This leads to plans that may contradict existing patterns or miss integration points.

## Solution

Add a `reference_docs` configuration section to `.code-forge.json` that automatically discovers project documentation via glob patterns, summarizes each doc using parallel sub-agents, and injects the summaries as context into plan generation.

## Design Decisions

### Reference docs are only needed at plan time

`plan.md` and `tasks/*.md` are the "compiled output" — reference context is baked into them during generation. Downstream skills (`impl`, `fixbug`, `review`) work from these files, not from raw docs. Therefore:

- Only `skills/plan/SKILL.md` needs workflow changes
- `impl`, `fixbug`, `review` remain unchanged
- No caching mechanism needed — plan runs once

### Per-doc sub-agents, not bulk loading

Each reference doc gets its own sub-agent that produces a ~300-500 byte structured summary. This means:

- Raw file size is irrelevant (sub-agent handles it in isolation)
- All sub-agents run in parallel (wall-clock time = single sub-agent)
- Main context stays lean (summaries only, not full docs)
- One failed file doesn't block the rest
- No need for `max_files` or `max_total_size_kb` limits

### No artificial limits

Glob patterns are the filter. Users control scope via pattern specificity. A runtime warning (> 30 files) provides safety without restricting large projects.

## Configuration Schema

Add to `.code-forge.json`:

```json
{
  "reference_docs": {
    "sources": ["docs/**/*.md", "specs/*.md"],
    "exclude": ["docs/plans/**"]
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sources` | `string[]` | `[]` | Glob patterns relative to project root. Empty = disabled |
| `exclude` | `string[]` | `[]` | Glob patterns to exclude from matches |

**System defaults:** `sources: []`, `exclude: []` — disabled unless explicitly configured. Backward compatible.

**Validation rules:**
- `sources` entries must NOT contain `..` (security)
- `sources` entries must NOT point to system directories (`node_modules/`, `.git/`, etc.)
- `sources` must be array of strings (fall back to `[]` on error)
- `exclude` must be array of strings (fall back to `[]` on error)
- Output directory (`{base_dir}/{output_dir}/**`) is auto-excluded

## Workflow: New Step 0.9

Inserted between Step 0 (config loading) and Step 0.8 (prompt mode).

**Updated execution order:**

```
0 → 0.9 (reference docs, if configured) → 0.8 (prompt mode only) → 1 → 2 → 3 → 4 → 6 → 7 → 5 → 8 → 8.5 → 9
```

### Step 0.9.1: Resolve Glob Patterns

1. Resolve each pattern in `sources` against project root
2. Apply `exclude` patterns
3. Auto-exclude `{base_dir}/{output_dir}/**` (prevent circular refs)
4. Deduplicate results
5. If 0 matches — display info message, continue without reference docs
6. If > 30 matches — display file list, ask user to confirm or refine

### Step 0.9.2: Display Matched Files

```
Reference docs: 6 files matched
  docs/architecture.md
  docs/api/endpoints.md
  docs/api/auth-flow.md
  docs/data-model.md
  docs/conventions.md
  specs/security-policy.md
```

Proceed directly — no confirmation needed (unless > 30 files).

### Step 0.9.3: Parallel Sub-agent Summarization

Spawn N parallel sub-agents via `Task` tool:

- `subagent_type`: `"general-purpose"`
- `description`: `"Summarize reference doc: {filename}"`

Each sub-agent reads one file and returns:

```
DOC_PATH: docs/architecture.md
DOC_TYPE: <architecture | api | requirements | conventions | data-model | other>
SUMMARY: <2-3 sentence summary>
KEY_DECISIONS: <bulleted list of important decisions/constraints/patterns>
RELEVANCE_TAGS: <comma-separated keywords>
```

### Step 0.9.4: Store Reference Summaries

Collect all sub-agent results into a `reference_summaries` list. Store in memory for Steps 2, 6, and 7.

### Step 0.9.5: Deduplicate Against Input Doc

When the input document path is known (after Step 1), remove it from `reference_summaries` if present — the feature doc is already read directly by Steps 2 and 6.

## Integration with Existing Steps

### Step 2 (Analyze Document) — sub-agent prompt addition

```
## Reference Context

The following project documents provide architectural context:

{reference_summaries}

Use these to align your analysis with existing project decisions and patterns.
```

### Step 6 (Generate plan.md) — sub-agent prompt addition

```
## Reference Context

{reference_summaries}

Ensure the implementation plan is consistent with existing architecture and conventions.
```

### Step 7 (Task Breakdown) — sub-agent prompt addition

```
## Reference Context

{reference_summaries}

Ensure task steps follow project conventions and integrate with existing components.
```

All three additions are conditional: only included when `reference_summaries` is non-empty.

## Error Handling

| Condition | Severity | Response |
|-----------|----------|----------|
| `sources` contains `..` | Error | Show error, fall back to `sources: []` |
| `sources` points to system dir | Error | Show error, fall back to `sources: []` |
| `sources` is not array | Error | Show error, fall back to `sources: []` |
| `exclude` is not array | Warning | Ignore `exclude`, use `[]` |
| 0 files matched | Info | Continue without reference docs |
| > 30 files matched | Prompt | Ask user to confirm or refine |
| Sub-agent failure on a file | Warning | Skip file, continue with rest |
| Binary/non-text file matched | Warning | Sub-agent fails, skip and warn |
| Input doc in reference list | Auto | Deduplicate silently |
| Output dir in sources | Auto | Auto-excluded silently |

## Files to Modify

| File | Changes |
|------|---------|
| `templates/.code-forge.json` | Add `reference_docs` section with empty defaults |
| `skills/plan/SKILL.md` | Add Step 0.9; update system defaults (Step 0.2), validation (Step 0.3), execution order comment; add `## Reference Context` to Steps 2, 6, 7 sub-agent prompts |
| `docs/CONFIGURATION.md` | Add `reference_docs` field documentation, configuration scenario, field details |

## Files NOT Modified

| File | Reason |
|------|--------|
| `skills/impl/SKILL.md` | Task files already contain baked-in reference context |
| `skills/fixbug/SKILL.md` | Works from plan.md which already reflects reference docs |
| `skills/review/SKILL.md` | Reviews against plan.md acceptance criteria, already contextualized |
| `skills/status/SKILL.md` | Status display has no need for reference docs |
| `commands/*.md` | Alias files route to skills, no changes needed |
