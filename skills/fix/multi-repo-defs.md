### Fix Multi-Repo Definitions

**Input parsing (MR-1):**
- `bug_description` — the bug to fix (required, everything before `--repos`). Can be prompt text or `@file` reference. A short version of this is the `{input_summary}` used throughout the protocol.
- Usage: `/code-forge:fix <bug-description> --repos <repo1> <repo2> [repo3...]`
- Example: `/code-forge:fix "connection pool exhaustion under load" --repos ~/api-python ~/api-typescript ~/api-rust`

**Readiness check (MR-2):**
- Verify directory is a valid git repo — that is sufficient
- No state.json or plan required (fix operates on any repo with the described bug)
- Detect primary language by checking for `Cargo.toml` (Rust), `package.json` (TypeScript/JS), `pyproject.toml`/`setup.py` (Python), `go.mod` (Go), `pom.xml` (Java)

**Summary table columns (MR-2):** `Language` — detected primary language of the repo (e.g., Python, TypeScript, Rust)

**Sub-agent prompt (MR-4):**

```
Fix this bug in the repository: '{bug_description}'

1. Scan the codebase for code related to the bug description
2. Diagnose the root cause (1-2 sentences)
3. Write a regression test that reproduces the bug (must fail before fix)
4. Implement the minimal fix
5. Run the full test suite to verify no regressions
6. Commit with message: fix: {brief description}
```

**Result format (MR-4 output):**

```
ROOT_CAUSE: <1-2 sentence root cause description>
FIX: <1-2 sentence description of what was changed>
FILES_CHANGED:
- path/to/file.ext (created | modified)
TEST_RESULTS: X passed, Y failed
```

**Report columns (MR-5):** `Root Cause` and `Tests` — e.g., "Race condition in pool" and "15 passed, 0 failed"

**Next steps (MR-5):**
- For partial repos: `/code-forge:fix "{bug_description}"` (in that repo to resume)
- General: `/code-forge:verify`
