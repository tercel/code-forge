# Reference Docs Auto-Discovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add configurable reference docs auto-discovery to code-forge so that `/code-forge:plan` automatically fetches project documentation as context for plan generation via parallel sub-agent summarization.

**Architecture:** New `reference_docs` config section in `.code-forge.json` with glob patterns. New Step 0.9 in plan skill resolves patterns, spawns parallel sub-agents to summarize each doc, and injects summaries into Steps 2/6/7. Downstream skills (impl, fixbug, review) are unchanged — reference context is baked into plan.md and task files.

**Tech Stack:** Markdown skill files, JSON config template, glob patterns

---

### Task 1: Add `reference_docs` section to config template

**Files:**
- Modify: `templates/.code-forge.json:35` (before closing brace)

**Step 1: Add the reference_docs section**

Edit `templates/.code-forge.json` — insert after the `execution` block (after line 35), before the closing `}`:

```json
  "execution": {
    "default_mode": "ask",
    "auto_tdd": true,
    "task_granularity": "medium"
  },

  "reference_docs": {
    "sources": [],
    "exclude": []
  }
}
```

Note: Add a comma after the `execution` closing brace. `sources` and `exclude` default to empty arrays (feature disabled).

**Step 2: Verify the JSON is valid**

Run: `python3 -c "import json; json.load(open('templates/.code-forge.json')); print('Valid JSON')"`
Expected: `Valid JSON`

**Step 3: Commit**

```bash
git add templates/.code-forge.json
git commit -m "feat: add reference_docs section to config template"
```

---

### Task 2: Update system defaults and validation in plan skill Step 0

**Files:**
- Modify: `skills/plan/SKILL.md:56` (Step 0.2 system defaults)
- Modify: `skills/plan/SKILL.md:64-68` (Step 0.3 validation rules)

**Step 1: Add reference_docs to system defaults**

Edit `skills/plan/SKILL.md` — in Step 0.2 system defaults list (after line 56, after the `execution` defaults), add:

```markdown
   - `reference_docs.sources` = `[]`, `reference_docs.exclude` = `[]`
```

**Step 2: Add reference_docs validation rules**

Edit `skills/plan/SKILL.md` — in Step 0.3 validation rules (after line 68, after the `execution.default_mode` rule), add:

```markdown
- `reference_docs.sources` must be an array of strings (fall back to `[]` on error)
- `reference_docs.sources` entries must NOT contain `..` (security risk)
- `reference_docs.sources` entries must NOT point to system directories (`node_modules/`, `.git/`, `build/`)
- `reference_docs.exclude` must be an array of strings (fall back to `[]` on error)
```

**Step 3: Verify changes read correctly**

Read the file and confirm the new lines are in the right location within their respective sections.

**Step 4: Commit**

```bash
git add skills/plan/SKILL.md
git commit -m "feat: add reference_docs defaults and validation rules to plan skill"
```

---

### Task 3: Insert new Step 0.9 into plan skill

**Files:**
- Modify: `skills/plan/SKILL.md:26` (execution order comment)
- Modify: `skills/plan/SKILL.md:95` (insert new step between Step 0 `---` divider and Step 0.8)

**Step 1: Update execution order comment**

Edit `skills/plan/SKILL.md` line 26 — replace:

```markdown
**Actual execution order:** 0 → 0.8 (prompt mode only) → 1 → **2 (sub-agent)** → 3 → 4 → **6 (sub-agent)** → **7 (sub-agent)** → 5 → 8 → 8.5 → 9
```

With:

```markdown
**Actual execution order:** 0 → **0.9 (reference docs, if configured)** → 0.8 (prompt mode only) → 1 → **2 (sub-agent)** → 3 → 4 → **6 (sub-agent)** → **7 (sub-agent)** → 5 → 8 → 8.5 → 9
```

**Step 2: Insert Step 0.9 block**

Edit `skills/plan/SKILL.md` — insert the following block after the `---` divider on line 95 (after Step 0.6) and before `### Step 0.8`:

```markdown
### Step 0.9: Resolve and Summarize Reference Docs

**This step only runs when `reference_docs.sources` is non-empty in the merged configuration.**

If `reference_docs.sources` is empty or not configured, skip directly to Step 0.8.

#### 0.9.1 Resolve Glob Patterns

1. Resolve each pattern in `config.reference_docs.sources` against `project_root`
2. Apply `config.reference_docs.exclude` patterns to filter results
3. Auto-exclude `{base_dir}/{output_dir}/**` to prevent circular references
4. Deduplicate results (same file matched by multiple patterns)
5. If 0 files matched → display: `Reference docs: 0 files matched for configured patterns. Continuing without reference context.` → skip to Step 0.8
6. If > 30 files matched → display file list, use `AskUserQuestion`: "Found {N} reference docs. This will spawn {N} parallel sub-agents."
   - "Proceed with all {N} files"
   - "Let me refine the patterns" → show current `sources`/`exclude` config, stop and let user update `.code-forge.json`

#### 0.9.2 Display Matched Files

Display the matched file list:
```
Reference docs: {count} files matched
  {path_1}
  {path_2}
  ...
```

Proceed directly — no confirmation needed (unless > 30 files triggered 0.9.1 step 6).

#### 0.9.3 Parallel Sub-agent Summarization

Spawn N parallel sub-agents via `Task` tool, one per matched file:

- `subagent_type`: `"general-purpose"`
- `description`: `"Summarize reference doc: {filename}"`

**Each sub-agent prompt:**
- The file path (sub-agent reads it from disk)
- Instruction to return ONLY a structured summary in this exact format:

```
DOC_PATH: {file_path}
DOC_TYPE: <architecture | api | requirements | conventions | data-model | other>
SUMMARY: <2-3 sentence summary of what this document describes>
KEY_DECISIONS: <bulleted list of important technical decisions, constraints, or patterns>
RELEVANCE_TAGS: <comma-separated keywords for matching against feature docs>
```

**Target summary size:** ~300-500 bytes per doc.

**Error handling:** If a sub-agent fails to summarize a file, log a warning and skip that file:
```
Warning: Failed to summarize {path} — skipping
Reference docs: {success_count} of {total_count} files summarized successfully
```

#### 0.9.4 Store Reference Summaries

Collect all successful sub-agent results into a `reference_summaries` list (ordered by file path). Store in memory for use by Steps 2, 6, and 7.

#### 0.9.5 Deduplicate Against Input Doc

After the input document path is known (after Step 1), remove it from `reference_summaries` if present — the feature doc is already read directly by Steps 2 and 6. This deduplication happens lazily: the summaries are stored now, deduplication is applied when injecting into sub-agent prompts.

---

```

**Step 3: Verify the new step is correctly positioned**

Read the file and confirm:
- Step 0.9 appears after the `---` divider following Step 0.6
- Step 0.8 follows after Step 0.9's `---` divider
- The step numbering is consistent

**Step 4: Commit**

```bash
git add skills/plan/SKILL.md
git commit -m "feat: add Step 0.9 reference docs resolution to plan skill"
```

---

### Task 4: Update Steps 2, 6, 7 sub-agent prompts to include reference context

**Files:**
- Modify: `skills/plan/SKILL.md:192-207` (Step 2 sub-agent prompt)
- Modify: `skills/plan/SKILL.md:249-254` (Step 6 sub-agent prompt)
- Modify: `skills/plan/SKILL.md:283-287` (Step 7 sub-agent prompt)

Note: Line numbers are approximate — they will shift after Task 3 inserts Step 0.9. Use the section headers to locate the correct positions.

**Step 1: Update Step 2 sub-agent prompt**

In `### Step 2: Analyze Document Content (via Sub-agent)`, find the line:

```markdown
**Sub-agent prompt must include:**
- The input document file path (so the sub-agent reads it, NOT the main context)
- Instruction to return ONLY a structured summary
```

Replace with:

```markdown
**Sub-agent prompt must include:**
- The input document file path (so the sub-agent reads it, NOT the main context)
- Instruction to return ONLY a structured summary
- If `reference_summaries` is non-empty (from Step 0.9), include a `## Reference Context` section:
  ```
  ## Reference Context

  The following project documents provide architectural context.
  Use these to align your analysis with existing project decisions and patterns.

  {reference_summaries — all summaries concatenated, separated by blank lines}
  ```
```

**Step 2: Update Step 6 sub-agent prompt**

In `### Step 6: Generate plan.md (via Sub-agent)`, find the line:

```markdown
**Sub-agent prompt must include:**
- The input document file path (sub-agent re-reads the original for full context)
- The structured summary from Step 2 (paste it into the prompt)
- User answers from Step 3 (tech stack choice, testing strategy, task granularity)
- The output file path: `{output_dir}/{feature_name}/plan.md`
- Instructions to write the plan file AND return a concise task list summary
```

Replace with:

```markdown
**Sub-agent prompt must include:**
- The input document file path (sub-agent re-reads the original for full context)
- The structured summary from Step 2 (paste it into the prompt)
- User answers from Step 3 (tech stack choice, testing strategy, task granularity)
- The output file path: `{output_dir}/{feature_name}/plan.md`
- Instructions to write the plan file AND return a concise task list summary
- If `reference_summaries` is non-empty, include a `## Reference Context` section:
  ```
  ## Reference Context

  The following project documents provide architectural context.
  Ensure the implementation plan is consistent with existing architecture and conventions.

  {reference_summaries — all summaries concatenated, separated by blank lines}
  ```
```

**Step 3: Update Step 7 sub-agent prompt**

In `### Step 7: Task Breakdown (via Sub-agent)`, find the line:

```markdown
**Sub-agent prompt must include:**
- The plan file path: `{output_dir}/{feature_name}/plan.md` (sub-agent reads it from disk)
- The task list summary returned by Step 6 (paste it into the prompt)
- The tasks directory path: `{output_dir}/{feature_name}/tasks/`
- All the principles and format requirements below
```

Replace with:

```markdown
**Sub-agent prompt must include:**
- The plan file path: `{output_dir}/{feature_name}/plan.md` (sub-agent reads it from disk)
- The task list summary returned by Step 6 (paste it into the prompt)
- The tasks directory path: `{output_dir}/{feature_name}/tasks/`
- All the principles and format requirements below
- If `reference_summaries` is non-empty, include a `## Reference Context` section:
  ```
  ## Reference Context

  The following project documents provide architectural context.
  Ensure task steps follow project conventions and integrate with existing components.

  {reference_summaries — all summaries concatenated, separated by blank lines}
  ```
```

**Step 4: Verify all three steps have the reference context addition**

Read the file and search for `## Reference Context` — should appear exactly 3 times (Steps 2, 6, 7).

**Step 5: Commit**

```bash
git add skills/plan/SKILL.md
git commit -m "feat: inject reference doc summaries into Steps 2, 6, 7 sub-agent prompts"
```

---

### Task 5: Update CONFIGURATION.md with reference_docs documentation

**Files:**
- Modify: `docs/CONFIGURATION.md:65` (Complete Configuration Example)
- Modify: `docs/CONFIGURATION.md:196` (after Scenario 5, add Scenario 6)
- Modify: `docs/CONFIGURATION.md:325` (after execution field details, add reference_docs)

**Step 1: Update Complete Configuration Example**

Edit `docs/CONFIGURATION.md` — in the Complete Configuration Example JSON block (around line 30-65), add the `reference_docs` section after `execution`:

```json
  "execution": {
    "default_mode": "ask",          // ask | manual | auto
    "auto_tdd": true,              // Auto-use TDD
    "task_granularity": "medium"   // fine | medium | coarse
  },

  "reference_docs": {
    "sources": [],                 // Glob patterns for project docs
    "exclude": []                  // Glob patterns to exclude
  }
```

Note: Add comma after `execution` closing brace.

**Step 2: Add Scenario 6**

Edit `docs/CONFIGURATION.md` — after Scenario 5 (Team Collaboration Mode, around line 196), add:

```markdown
### Scenario 6: Auto-load Project Documentation as Reference

Use existing project docs as context for plan generation:

```json
{
  "reference_docs": {
    "sources": ["docs/**/*.md", "specs/*.md"],
    "exclude": ["docs/plans/**", "docs/internal/**"]
  }
}
```

**Result:**
When running `/code-forge:plan`, code-forge will:
1. Discover all `.md` files in `docs/` and `specs/` (excluding `docs/plans/` and `docs/internal/`)
2. Spawn parallel sub-agents to summarize each doc (~300-500 bytes each)
3. Inject summaries as context into plan generation sub-agents
4. Generated `plan.md` and `tasks/*.md` will reflect existing architecture and conventions

**Note:** Reference docs are only used at plan time. The generated plan and task files already contain baked-in context — downstream skills (`impl`, `fixbug`, `review`) do not re-read reference docs.
```

**Step 3: Add reference_docs field details**

Edit `docs/CONFIGURATION.md` — after the `execution` field details section (around line 343), add:

```markdown
### reference_docs

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sources` | string[] | `[]` | Glob patterns relative to project root for docs to include as reference context. Empty = disabled |
| `exclude` | string[] | `[]` | Glob patterns to exclude from matches |

**How it works:**
- At plan time (Step 0.9), glob patterns are resolved against the project root
- Each matched file is summarized by a parallel sub-agent (~300-500 bytes each)
- Summaries are injected as context into plan generation sub-agents (Steps 2, 6, 7)
- Generated plans and task files contain baked-in reference context
- Downstream skills (impl, fixbug, review) work from these files — no re-reading needed

**Auto-exclusions:**
- The output directory (`{base}/{output}/**`) is always excluded to prevent circular references
- The input feature document is deduplicated from reference docs

**Runtime safety:**
- If > 30 files match, user is prompted to confirm or refine patterns
- If a file fails to summarize, it is skipped with a warning — other files continue

**Examples:**
```json
// Include all markdown in docs/
{
  "reference_docs": {
    "sources": ["docs/**/*.md"]
  }
}

// Multiple directories with exclusions
{
  "reference_docs": {
    "sources": ["docs/**/*.md", "specs/*.md", "architecture/*.md"],
    "exclude": ["docs/plans/**", "docs/drafts/**"]
  }
}

// Specific files only
{
  "reference_docs": {
    "sources": ["docs/architecture.md", "docs/api-design.md"]
  }
}

// Disable (default)
{
  "reference_docs": {
    "sources": []
  }
}
```
```

**Step 4: Update the Summary table at the end of the file**

Edit `docs/CONFIGURATION.md` — in the Summary table (around line 547), add a row:

```markdown
| ⭐⭐⭐ | `reference_docs.sources: ["docs/**/*.md"]` | Projects with existing architecture docs |
```

**Step 5: Verify the documentation reads well**

Read the full CONFIGURATION.md and verify:
- Complete Configuration Example includes `reference_docs`
- Scenario 6 appears after Scenario 5
- `reference_docs` field details appear after `execution` field details
- Summary table includes the new row

**Step 6: Commit**

```bash
git add docs/CONFIGURATION.md
git commit -m "docs: add reference_docs configuration documentation"
```

---

### Task 6: Update plan skill Notes section

**Files:**
- Modify: `skills/plan/SKILL.md:419-443` (Notes section at end of file)

**Step 1: Add reference docs note**

Edit `skills/plan/SKILL.md` — in the Notes section (after note 11, at the end of the file), add:

```markdown
12. **Reference Docs**: Configure `reference_docs.sources` in `.code-forge.json` to auto-discover project documentation. Each doc is summarized by a parallel sub-agent and injected as context into Steps 2, 6, and 7. Reference context is baked into generated plan.md and task files — downstream skills do not re-read reference docs.
```

**Step 2: Commit**

```bash
git add skills/plan/SKILL.md
git commit -m "docs: add reference docs note to plan skill"
```

---

### Task 7: Final verification

**Step 1: Verify JSON template is valid**

Run: `python3 -c "import json; json.load(open('templates/.code-forge.json')); print('Valid JSON')"`
Expected: `Valid JSON`

**Step 2: Verify plan skill has all expected sections**

Run a search for key markers in `skills/plan/SKILL.md`:
- `### Step 0.9` — exists once
- `reference_docs.sources` — exists in Steps 0.2, 0.3, 0.9
- `## Reference Context` — exists 3 times (Steps 2, 6, 7)
- `0.9 (reference docs` — exists in execution order comment

**Step 3: Verify CONFIGURATION.md has all expected sections**

Run a search for key markers in `docs/CONFIGURATION.md`:
- `reference_docs` — exists in Complete Example, Scenario 6, Field Details, Summary
- `Scenario 6` — exists once

**Step 4: Commit any remaining changes**

If any corrections were needed, commit with:
```bash
git add -A && git commit -m "fix: address verification issues in reference docs implementation"
```

**Step 5: Final summary commit (if all individual commits were made)**

No squash needed. The commit history tells the story:
1. `feat: add reference_docs section to config template`
2. `feat: add reference_docs defaults and validation rules to plan skill`
3. `feat: add Step 0.9 reference docs resolution to plan skill`
4. `feat: inject reference doc summaries into Steps 2, 6, 7 sub-agent prompts`
5. `docs: add reference_docs configuration documentation`
6. `docs: add reference docs note to plan skill`
