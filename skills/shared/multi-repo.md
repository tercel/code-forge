### Multi-Repo Flow Protocol

**Purpose:** Coordinate execution of a skill across multiple repositories in parallel. Referenced by skills that support a `--repos` flag. The calling skill defines its specific input parsing, readiness criteria, sub-agent prompt, and result format after this reference.

**When entered:** The calling skill detects `--repos` in `$ARGUMENTS` and jumps to this flow. Standard single-repo steps are skipped entirely.

---

#### Skill-Specific Definitions Required

The skill-specific definitions file (read alongside this protocol) MUST define:

1. **Input parsing** — what arguments precede `--repos` (e.g., feature name, bug description). The primary input is referred to as `{input_summary}` throughout this protocol (e.g., the feature name or a short bug description).
2. **Readiness check** — what makes a repo "ready" for this skill
3. **Summary table columns** — what extra columns to show per repo beyond Repo / Path / Status
4. **Sub-agent prompt** — the task-specific instructions. These are inserted into the `## Task` section of the prompt template in MR-4, which provides the wrapper (working directory, execution rules, coding standards, output format).
5. **Result format** — what structured fields each sub-agent returns (inserted into the `## Output Required` section)
6. **Next steps** — what commands to suggest after completion

---

#### MR-1: Parse Arguments

Extract from `$ARGUMENTS`:
- **Skill-specific input** — [Skill defines: what precedes `--repos`]
- `--repos` — space-separated list of repository paths (at least 1)

If arguments are missing or malformed, show the skill-specific usage example.

Resolve all repo paths to absolute paths (expand `~` to the user's home directory). Verify each directory exists and is a git repository (`git -C {path} rev-parse --git-dir`).

---

#### MR-2: Scan and Validate Repos

For each repo path:

1. Detect the project's code-forge configuration (`.code-forge.json`, fall back to defaults)
2. Determine `output_dir` (default: `planning/`)
3. **[Skill defines: readiness check]** — apply the skill's readiness criteria
4. Collect per-repo metadata for the summary table

Display a summary table:

```
{skill_name} --repos: {input_summary} across {N} repos

  Repo              Path                   Status       [Skill-specific columns]
  repo-name         ~/path/to/repo         Ready        ...
  repo-name-2       ~/path/to/repo-2       NOT READY    (reason)
```

**If any repo is not ready:**
- Show which repos failed and why
- Ask via `AskUserQuestion`:
  - **"Proceed with ready repos only"** — skip unready repos
  - **"Abort"** — exit, suggest how to make repos ready

**If all repos already completed** (per [Skill defines: readiness check] criteria): Show completion message, suggest next steps.

---

#### MR-3: Confirm Execution

Use `AskUserQuestion`:

- **"Parallel Execution (Recommended)"** — dispatch all repo agents simultaneously
- **"Sequential Execution"** — execute repos one by one (safer, easier to debug)
- **"Abort"** — exit without executing

---

#### MR-4: Dispatch Repo Sub-agents

##### MR-4.1 Parallel Mode (Recommended)

**Launch ALL repo sub-agents in a SINGLE message** using multiple `Agent` tool calls. This enables true parallel execution.

For each ready repo, spawn an `Agent` tool call with:
- `subagent_type`: `"general-purpose"`
- `description`: `"{skill_name} {input_summary} in {repo_name}"`

**Sub-agent prompt structure:**

```
You are running {skill_name} in the repository at {repo_absolute_path}.

## Task
[Insert the skill-specific sub-agent prompt from the definitions file here]

## Working Directory
Your working directory is: {repo_absolute_path}
All file operations must be relative to this directory.

## Execution Rules
- Before making changes, check the current branch. If on `main` or `master`, create a feature branch (e.g., `impl/core-dispatcher` or `fix/connection-pool-leak`). Slugify the name: lowercase, replace spaces with hyphens, strip special characters.
- Skip user confirmation prompts — execute directly
- Follow the task instructions above within this repo
- Commit changes with descriptive messages after tests pass

## Coding Standards
(Coordinator: read `coding-standards.md` from the same directory where you found this `multi-repo.md` file, and paste its full contents here verbatim.)

## Output Required
Return ONLY a concise execution summary:

REPO: {repo_name}
STATUS: completed | partial | blocked
[Skill defines: result format fields]
SUMMARY: <1-2 sentence description>
ISSUES: <blockers or "none">
```

##### MR-4.2 Sequential Mode

Execute repos one by one in the order provided. For each repo:
1. Display: "Starting: {repo_name} ({index}/{total})"
2. Dispatch a single sub-agent (same prompt as MR-4.1)
3. Wait for completion, display summary
4. Ask via `AskUserQuestion`:
   - **"Continue to next repo"** — proceed
   - **"Pause"** — exit loop, show resume instructions
5. Repeat for next repo

---

#### MR-5: Collect Results and Report

After all sub-agents complete (or fail):

1. **Parse each sub-agent's execution summary.** If a sub-agent returned malformed output or failed entirely, mark that repo as `STATUS: error` with the raw error message as the issue.

2. **Display cross-repo report:**

```
{skill_name} --repos complete: {input_summary}

  Repo              Status       [Skill-specific result columns]
  repo-name         completed    ...
  repo-name-2       partial      ...

Overall: {completed_count}/{total_count} repos completed
```

3. **If any repo has issues**, list them with repo name and error details.

4. **Suggest next steps:** [Skill defines: next step commands per repo status]
