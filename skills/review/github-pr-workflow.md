# GitHub PR Review Workflow

Post a 15-dimension code review directly to a GitHub Pull Request as a comment.

## Prerequisites

- `gh` CLI installed and authenticated
- Current directory inside a git repository with a GitHub remote

## Workflow

```
Resolve PR → Fetch Diff → Detect Project Type → 14-Dimension Review (sub-agent) → Filter → Format → Post
```

## Steps

### Step 1: Resolve the Pull Request

Determine which PR to review:

1. **Explicit PR number** — user passed `--github-pr 123` or `--github-pr #123` → use that number
2. **No number** — auto-detect from current branch:
   ```bash
   gh pr view --json number,url,headRefName,baseRefName,title,state --jq '.'
   ```
   - If no PR found: error — "No open PR found for the current branch. Specify a PR number: `/code-forge:review --github-pr 123`"
   - If PR is closed/merged: error — "PR #{number} is already {state}."
   - If PR is draft: warn but continue — "Note: PR #{number} is a draft."

Record: `pr_number`, `pr_url`, `head_branch`, `base_branch`, `pr_title`

### Step 2: Fetch PR Diff and Metadata

Run in parallel:

1. **Get the diff:**
   ```bash
   gh pr diff {pr_number}
   ```

2. **Get changed files list with full paths:**
   ```bash
   gh pr diff {pr_number} --name-only
   ```

3. **Get the HEAD commit full SHA** (for GitHub file links):
   ```bash
   gh pr view {pr_number} --json headRefOid --jq '.headRefOid'
   ```

4. **Get repository owner/name:**
   ```bash
   gh repo view --json nameWithOwner --jq '.nameWithOwner'
   ```

Record: `diff_content`, `changed_files`, `head_sha` (full 40-char), `repo_slug` (owner/name)

### Step 3: Detect Project Type

Same as the main review skill's project type detection (Step 3F.2 / 3P.2):
- Check changed files for frontend indicators (`.tsx`, `.jsx`, `.vue`, `.svelte`, CSS)
- Check for backend indicators (server entries, API routes, DB models)
- Record: `project_type`

### Step 4: 15-Dimension Review (via Sub-agent)

Spawn an `Agent` sub-agent with `subagent_type: "general-purpose"`.

**Sub-agent prompt must include:**

- PR title and number
- Base branch and head branch
- The full diff content
- List of changed files (sub-agent reads each file for full context)
- Detected project type
- **All 15 review dimensions** from the main SKILL.md's [Review Dimensions Reference]
- The 4-tier severity definitions (blocker / critical / warning / suggestion)
- **MANDATORY pre-analysis instruction:** *"Before applying any review dimension, read every changed file in full and build a call graph for every public method / exported function touched by the diff. Enumerate helpers called, validations performed, state mutations executed, errors raised, and external-input paths. Output as `METHOD_CHAINS` per `references/sub-agent-format.md`. Only after producing METHOD_CHAINS may you apply dimensions. Scope note: the graph is rooted at symbols MODIFIED by the diff — not every public symbol in every changed file. Do not trust method names or helper-function purity — open and read every callee. See the §Call-Graph Discipline section of the main review SKILL.md."*
- Instruction: **"Review ONLY the changes in this PR diff. Do not flag pre-existing issues. For each issue, specify severity, file path, line number/range, title, description, and fix suggestion. When an issue was discovered via the call graph, reference the relevant METHOD_CHAINS entry."**

**Sub-agent must return the same structured format** as the main review skill (REVIEW_SUMMARY + per-dimension sections + **METHOD_CHAINS**). The orchestrator MUST verify METHOD_CHAINS is populated (covers every diff-modified public symbol) before posting to GitHub — a review posted to a public PR without the pre-analysis would be worse than no review because reviewers would wrongly trust its completeness. If the sub-agent fails the METHOD_CHAINS check twice, abort the post and surface the failure locally; do NOT post an incomplete review to the PR.

### Step 5: Filter Issues for GitHub

GitHub PR comments should be high-signal, not noisy. Apply filtering:

1. **Include:** All `blocker`, `critical`, and `warning` issues
2. **Exclude:** `suggestion` severity (these are nice-to-have and create noise on PRs)
3. **Exclude:** Issues on lines NOT changed in this PR (pre-existing issues)
4. If zero issues remain after filtering → post the "no issues" comment (Step 6.2)

### Step 6: Format and Post

#### 6.1 Issues Found

Format the comment body:

```markdown
### Code Review — {pr_title}

**15-dimension review** · {blocker_count} blockers · {critical_count} critical · {warning_count} warnings
**Merge readiness:** {ready | fix_required | rework_required}

---

{For each issue, ordered by severity (blockers first):}

**{severity_badge} {title}** — `{file_path}`

{description}

{suggestion}

[View code](https://github.com/{repo_slug}/blob/{head_sha}/{file_path}#L{start}-L{end})

---

{Final verdict: 1-2 sentences summarizing whether the PR is ready to merge}

<sub>🤖 Generated with [Claude Code](https://claude.ai/code) · code-forge:review · 15 dimensions · {total_issues_posted} issues</sub>
```

**Severity badges:**
- `blocker` → `🚫 BLOCKER`
- `critical` → `⚠️ CRITICAL`
- `warning` → `🟠 WARNING`

**File link format** — use full 40-character SHA with line range context (at least 1 line before and after):
```
https://github.com/{repo_slug}/blob/{head_sha}/{file_path}#L{start}-L{end}
```

#### 6.2 No Issues Found

```markdown
### Code Review — {pr_title}

No issues found. Reviewed across 15 dimensions: functional correctness, security, resource management, code quality, architecture, performance, test coverage, simplification & anti-bloat, error handling, observability, standards, backward compatibility, maintainability, dependencies, and accessibility.

<sub>🤖 Generated with [Claude Code](https://claude.ai/code) · code-forge:review</sub>
```

#### 6.3 Post the Comment

Post using `gh`:

```bash
gh pr comment {pr_number} --body "{formatted_comment}"
```

Use a heredoc for the body to handle multi-line content and special characters:

```bash
gh pr comment {pr_number} --body "$(cat <<'REVIEW_EOF'
{formatted_comment}
REVIEW_EOF
)"
```

### Step 7: Terminal Summary

After posting, display in the terminal:

```
GitHub PR Review Posted: #{pr_number}

PR: {pr_title}
URL: {pr_url}
Merge Readiness: {merge_readiness}
Issues Posted: {total_issues_posted} ({blocker_count} blockers, {critical_count} critical, {warning_count} warnings)
Suggestions Filtered: {suggestion_count} (not posted — use local review for full report)

{If fix_required or rework_required:}
🚫 Merge blocked — fix these first:
  1. {top issue with file:line}
  2. ...

{If ready:}
✅ PR looks good — ready to merge.

Tip: Run /code-forge:review [feature] for the full local report including suggestions.
```

## Error Handling

- **`gh` not installed:** "Error: `gh` CLI not found. Install it: https://cli.github.com/"
- **Not authenticated:** "Error: `gh` not authenticated. Run `gh auth login` first."
- **No GitHub remote:** "Error: No GitHub remote found in this repository."
- **PR not found:** "Error: PR #{number} not found. Check the number and try again."
- **Comment post fails:** Show the formatted comment in the terminal as fallback and display the `gh` error.
