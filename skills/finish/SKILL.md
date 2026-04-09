---
name: finish
description: >
  Use when implementation is complete and you need to merge, create a PR, or clean up —
  verifies tests pass, presents 4 structured integration options, executes chosen workflow,
  and cleans up worktrees. Pairs with code-forge:worktree.
---

# Code Forge — Finish

## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read Step 1 (Verify Tests), perform it, then Step 1.5 (Simplification Gate), then Step 2, etc., until the workflow completes or you reach an `AskUserQuestion` checkpoint.

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual finish", "回退到手动 finish", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to Step 1 and start executing.

The first user-visible action of this skill should be either (a) the output of Step 1 / Step 1.5 of the workflow, or (b) an `AskUserQuestion` if a step needs disambiguation. Never an apology, never a fallback, never silence.

---

Complete a development branch by verifying tests, choosing an integration strategy, and cleaning up.

## When to Use

- Implementation is complete and all tasks are done
- After code-forge:impl finishes all tasks for a feature
- When you need to integrate a feature branch back to main
- When you want to discard experimental work cleanly

## Workflow

```
Verify Tests → Simplification Gate → Determine Base Branch → Present 4 Options → Execute Choice → Cleanup Worktree
```

### Step 1: Verify Tests

Run the full test suite before proceeding (following the `code-forge:verify` discipline — run fresh, read full output, confirm zero failures).

```bash
# Auto-detect and run test command
```

- **All pass:** Proceed to Step 1.5
- **Any fail:** **STOP.** Do not proceed. Report failures and suggest fixes.

### Step 1.5: Simplification Gate (Mandatory Pre-Merge Cleanup)

**This step is mandatory and runs on every `/code-forge:finish` invocation.** It is the last line of defense against merging bloated, redundant, or dead code that slipped past the planner and the reviewer. Skill-driven feature work has a strong additive bias — this gate is what keeps the codebase from growing unbounded across feature cycles.

The gate is fully self-contained — it does not depend on any external skill. The detection criteria, fix rules, and safety constraints are all defined inline below.

#### 1.5.1 Compute Diff Scope

```bash
# Determine base branch
BASE_BRANCH=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null | sed 's|origin/||' || echo "main")

# List files changed since branching from base
git diff --name-only "${BASE_BRANCH}...HEAD"
```

If the changed file list is empty (nothing to merge), skip the gate and proceed to Step 2.

#### 1.5.2 Pre-Gate Safety Check

**Before running the gate, capture the working-tree state** so we can distinguish simplification changes from any other uncommitted changes the user may have:

```bash
git status --porcelain > /tmp/code-forge-finish-pre-gate-status.txt
```

If `/tmp/code-forge-finish-pre-gate-status.txt` is non-empty (the user already has uncommitted work before the gate runs), display a warning and use `AskUserQuestion`:
- "Stash them and run the gate" → run `git stash push -u -m "code-forge-finish-pre-gate"`, then proceed; pop the stash before exiting Step 1.5
- "Commit them first, then run the gate" → STOP, let the user commit, ask the user to re-run `/code-forge:finish`
- "Proceed without stashing (risky — gate fixes will mix with your changes)" → proceed; the cleanup logic in 1.5.3 will then refuse the destructive options and only allow "review and decide manually"

#### 1.5.3 Run the Simplification Sub-agent

**Offload to a sub-agent** so the full diff, grep output, and file reads stay out of the main context.

Spawn an `Agent` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"Pre-merge simplification gate"`

**Sub-agent prompt must include all of the following, verbatim, plus the base branch name and the changed-file list from 1.5.1:**

```
You are the pre-merge simplification gate for code-forge:finish.

Your job is to scan the diff between {BASE_BRANCH} and HEAD for bloat introduced by
this branch, fix what is safe to fix automatically, and report the rest. You operate
ONLY on the files listed in CHANGED_FILES below — do not touch anything else.

CHANGED_FILES:
{paste the file list from 1.5.1}

═══ DETECTION CRITERIA ═══

Review every file in CHANGED_FILES against these seven categories. For each finding,
classify it and decide whether you can fix it automatically or whether it needs human
judgment.

(a) DUPLICATE — code in this diff that reimplements something already present elsewhere
    in the project. Before flagging, run `Grep` for similar names, similar signatures,
    and similar string literals across the project. If a near-equivalent exists, the
    new code is a duplicate.
    Auto-fix: replace callers of the new symbol with the existing symbol, then delete
    the new symbol. Only do this when the existing symbol's behavior is provably
    equivalent — otherwise leave for human.

(b) DEAD_CODE — new symbols (functions, classes, types, constants, exports) defined in
    the diff that have zero callers anywhere in the project. Use `Grep` across the
    full project (not just CHANGED_FILES) to verify there are no external callers.
    Auto-fix: delete the symbol and any tests that exist solely for it.

(c) SPECULATIVE_ABSTRACTION — new base classes, interfaces, plugin systems, generics,
    factories, or "extension points" introduced with exactly one (or zero) current
    call sites. These are added "for future flexibility" but rarely pay off.
    Auto-fix: inline back to the concrete implementation if the abstraction has
    exactly one caller. Leave for human if it has zero callers (likely related to
    DEAD_CODE) or any meaningful subclassing.

(d) WRAPPER — new functions whose entire body is a single call to another function
    with the same arguments, or that only rename fields without adding logic.
    Auto-fix: inline the wrapper at every call site, delete the wrapper.

(e) SCOPE_CREEP — files, modules, or public APIs introduced by this branch that are
    not traceable to any task in the feature's plan.md (look for plan.md under
    `planning/{feature_name}/` or `.code-forge/tmp/{feature_name}/`). If no plan.md
    exists, skip this category.
    Auto-fix: NEVER. Always leave for human — scope decisions are not safe to
    automate.

(f) STALE — within CHANGED_FILES, look for unused imports, commented-out code blocks
    (≥ 5 lines), unreachable branches, and TODO/FIXME/HACK comments without
    actionable context that this branch touches.
    Auto-fix: delete unused imports, delete commented-out blocks, delete unreachable
    branches. Leave actionable TODOs alone.

(g) DEFENSIVE — try/except blocks, null checks, or fallbacks that guard scenarios the
    type system or upstream invariants already make impossible (e.g., a null check on
    a parameter that the type system marks non-nullable, a try/except around a pure
    function that cannot raise).
    Auto-fix: delete the defensive code. Only do this when you are certain the
    guarded scenario is unreachable; otherwise leave for human.

═══ FIX RULES (apply in order) ═══

1. Apply fixes ONLY to files in CHANGED_FILES. Never modify files outside this list,
   even if you spot bloat there — surface it as REMAINING_ISSUES instead so the user
   can decide whether to expand the scope.
2. Apply DEAD_CODE and STALE fixes first (lowest risk).
3. Then WRAPPER and SPECULATIVE_ABSTRACTION fixes.
4. Then DUPLICATE fixes (highest risk — verify equivalence first).
5. NEVER apply SCOPE_CREEP fixes automatically.
6. After every batch of fixes, re-run the full test suite (auto-detect: pytest |
   npx vitest run | go test ./... | cargo test | mvn test | gradle test | dotnet test
   | swift test | vendor/bin/phpunit | mix test).
7. If any test fails: identify which fix caused it. Revert ONLY that fix using
   `git checkout HEAD -- <specific-file>`. Never use wildcards. Re-run the tests
   until they pass. If you cannot isolate the offending fix, revert ALL fixes you
   applied in this run (one file at a time, by name) and report the failure.
8. Track every file you modify in `FIXES_APPLIED.file`. The orchestrator uses this
   list as the sole source of truth for what to commit or revert — if you forget a
   file, the orchestrator will not commit it.

═══ HARD CONSTRAINTS ═══

- Never run `git add -A`, `git checkout -- .`, `git reset --hard`, `git clean`, or
  any other wildcard git command. Every git operation must name specific files.
- Never commit, never push, never merge. Leave all surviving fixes uncommitted in
  the working tree.
- Never modify a file outside CHANGED_FILES, even to fix something obviously broken.
  Report it in REMAINING_ISSUES instead.
- Never delete a file the user authored on this branch unless it is provably dead
  (zero callers anywhere, no tests, no exports).

═══ REQUIRED OUTPUT FORMAT ═══

Return exactly the structure defined in "Sub-agent return format" below
(no preamble, no postscript). The orchestrator parses it field by field.
```

**Sub-agent return format:**

```
GATE_REPORT

DIFF_SCOPE:
  base: {base_branch}
  files_changed: {N}
  loc_added: {N}
  loc_removed: {N}

FINDINGS:
- severity: critical | warning | suggestion
  category: duplicate | dead_code | speculative_abstraction | wrapper | scope_creep | stale | defensive | other
  file: {path:line}
  detail: {what's wrong}
  action: {fixed | needs_human_decision | left_alone}

FIXES_APPLIED:
- file: {path}
  category: {category}
  description: {what was changed}

TESTS_AFTER_FIX:
  status: pass | fail | skipped
  passed: {N}
  total: {N}

REMAINING_ISSUES:
- {issues that need human decision before merge}

NET_LOC_DELTA: {original loc_added minus lines removed by gate fixes}
```

#### 1.5.4 Decision

Read the report from the sub-agent and act. **The set of files the sub-agent touched comes ONLY from `FIXES_APPLIED.file` in the report — never from `git status`, never from a wildcard.** This isolation is what makes the gate safe to run on a working tree that may also contain unrelated user changes.

Build `GATE_FILES` = the deduplicated list of file paths from `FIXES_APPLIED.file`.

- **No findings, no fixes applied (`FIXES_APPLIED` is empty):** Display `Simplification gate: clean. No bloat detected.` If we stashed in 1.5.2, `git stash pop`. Proceed to Step 2.

- **Fixes applied, all tests still pass:** Display the `FIXES_APPLIED` list and the new `NET_LOC_DELTA`. Use `AskUserQuestion` to ask:
  - **"Review the simplification changes"** → run `git diff -- $GATE_FILES` (only the gate files), display the summary, then re-ask the same question.
  - **"Commit the simplifications, then proceed to merge options"** → stage ONLY the gate files explicitly: `git add -- $GATE_FILES`. Then commit: `git commit -m "chore: pre-merge simplification gate"`. If the gate was preceded by a stash (1.5.2), `git stash pop` AFTER the commit so the user's prior work returns to the working tree unmixed with the gate commit. Proceed to Step 2.
  - **"Discard the simplifications and proceed anyway"** → use `AskUserQuestion` to confirm with a separate "Yes, discard" / "Cancel" choice. On confirmation, revert ONLY the gate files: `git checkout HEAD -- $GATE_FILES`. **Never** run `git checkout -- .` or `git reset --hard` — those would destroy unrelated user changes. If we stashed in 1.5.2, `git stash pop`. Proceed to Step 2.
  - **If the user chose "Proceed without stashing" in 1.5.2**: omit the "Discard the simplifications" option entirely — the working tree contains mixed changes and a surgical revert is unsafe without the user picking files manually. Only offer "Review", "Commit", and "Stop and resolve manually".

- **Tests broke after fixes (sub-agent should have already reverted the offending fix):** Display the failing test name, the reverted fix, and the remaining `FIXES_APPLIED` entries. **STOP.** Do not proceed to Step 2. The user must verify the working tree manually and re-run `/code-forge:finish`.

- **`REMAINING_ISSUES` is non-empty (unfixable bloat that needs human judgment):** Display them with `file:line` references. Use `AskUserQuestion`:
  - "Address remaining issues now (recommended)" → STOP. If we stashed in 1.5.2, leave the stash in place and tell the user the stash name so they can pop it after resolving.
  - "Proceed to merge options anyway (issues will land in main)" → continue with the "Fixes applied" flow above for any fixes the gate did apply, then proceed to Step 2 with a warning.

**Hard rule:** The simplification gate is never silently skipped. Even if the diff is small. Even if the user is in a hurry. Skipping requires the explicit user choice "Proceed to merge options anyway". And under no circumstance does the gate use destructive wildcard git commands (`git checkout -- .`, `git reset --hard`, `git add -A`, `git clean`) — every operation is scoped to `GATE_FILES`.

### Step 2: Determine Base Branch

```bash
# Find the upstream branch this was created from
BASE_BRANCH=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null | sed 's|origin/||' || echo "main")
```

### Step 3: Present Exactly 4 Options

Present these options to the user using `AskUserQuestion`. Do NOT modify, add, or remove options:

**Option 1: Merge back to {base-branch} locally**
- `git checkout {base-branch} && git merge {feature-branch}`
- Best when: working solo, no review needed

**Option 2: Push and create Pull Request**
- `git push -u origin {feature-branch}` then `gh pr create`
- Best when: team workflow, review required

**Option 3: Keep branch as-is**
- No action taken, worktree preserved
- Best when: work in progress, will continue later

**Option 4: Discard this work**
- Requires typing "discard" to confirm
- Removes branch and all changes permanently

### Step 4: Execute Choice

**Option 1 — Merge:**
```bash
# If inside a worktree, cd to the main repo first
MAIN_REPO=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel 2>/dev/null)
if [ -n "$MAIN_REPO" ] && [ "$MAIN_REPO" != "$(git rev-parse --show-toplevel)" ]; then
  cd "$MAIN_REPO"
fi
git checkout {base-branch}
git merge {feature-branch} --no-ff
```

**Option 2 — Push + PR:**
```bash
git push -u origin {feature-branch}
gh pr create --title "{feature-name}: <summary>" --body "$(cat <<'EOF'
## Summary
<generated from commits>

## Test plan
- [ ] All tests pass

Generated with [code-forge](https://github.com/anthropics/claude-code)
EOF
)"
```
Report the PR URL to the user.

**Option 3 — Keep:**
No action. Report current branch and worktree location.

**Option 4 — Discard:**
Ask user to type "discard" to confirm. Then:
```bash
git checkout {base-branch}
git branch -D {feature-branch}
```

### Step 5: Cleanup Worktree

**Options 1, 2, 4:** Detect if inside a worktree and remove it:
```bash
# Detect worktree: if git-common-dir differs from git-dir, we are in a worktree
COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
if [ "$COMMON_DIR" != "$GIT_DIR" ]; then
  WORKTREE_PATH=$(pwd)
  cd $(git -C "$COMMON_DIR/.." rev-parse --show-toplevel)
  git worktree remove "$WORKTREE_PATH"
fi
```

**Option 3:** Do NOT clean up. The worktree stays.

### Step 6: Cleanup Temporary Plan Files

If the feature's plan was stored in `.code-forge/tmp/` (created with `--tmp`):

1. After successful merge (Option 1) or PR creation (Option 2) or discard (Option 4): delete `.code-forge/tmp/{feature_name}/`
2. If `.code-forge/tmp/` is now empty, remove `.code-forge/tmp/`. If `.code-forge/` is also now empty, remove it too.
3. Display: `Cleaned up temporary plan files: .code-forge/tmp/{feature_name}/`

**Option 3 (Keep):** Do NOT clean up — the tmp plan files stay for future `/impl` sessions.

### Completion Report

```
Branch finished:
  Feature:   {feature-name}
  Action:    {Merged / PR created / Kept / Discarded}
  PR URL:    {url} (Option 2 only)
  Worktree:  {removed / preserved}
  Tmp plan:  {cleaned up / preserved} (only shown for --tmp plans)
```

## Example

```
$ /code-forge:finish

Tests: 42/42 passing ✓

How would you like to integrate this branch?
  1. Merge back to main locally
  2. Push and create Pull Request
  3. Keep branch as-is
  4. Discard this work

> 2

Branch finished:
  Feature:   user-auth
  Action:    PR created
  PR URL:    https://github.com/org/repo/pull/47
  Worktree:  removed
```

## Common Mistakes

- Proceeding without verifying tests pass
- Skipping the Step 1.5 simplification gate — it is mandatory
- Silently discarding the simplification fixes without asking the user
- Using `git checkout -- .`, `git add -A`, `git reset --hard`, or any other wildcard git operation in Step 1.5 — every command must be scoped to `GATE_FILES` (the explicit list returned by the sub-agent in `FIXES_APPLIED.file`)
- Skipping the 1.5.2 pre-gate safety check (stashing prior uncommitted work) — running the gate on a working tree with unrelated changes mixes the gate commit with user work
- Proceeding past Step 1.5 when tests broke after a simplification (the sub-agent should have reverted, but if it didn't, STOP)
- Modifying the 4 options (adding, removing, or reordering)
- Cleaning up worktree when user chose "Keep"
- Executing discard without explicit "discard" confirmation
