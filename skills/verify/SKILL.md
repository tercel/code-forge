---
name: verify
description: >
  Use before claiming ENGINEERING WORK is done, fixed, or passing — work whose correctness a
  command can demonstrate (tests, build, lint, type-check, a CLI run, a request against a
  running service). Requires running that command fresh and reading its output before any
  success claim. Prevents false completion claims, unverified assertions, and "should work".
  Do NOT use for verification that has no command to run — fact-checking a statement,
  confirming a document is accurate or complete, reconciling numbers in a spreadsheet,
  double-checking a translation, or "验证一下这个说法对不对". There is nothing to execute there,
  so this skill does not apply; check the source directly instead.
---

# Code Forge — Verify

## ⚡ Execution Entry Point

@../shared/execution-entrypoint.md

**For this skill:** start at **the first executable step**. If you catch yourself about to say "falling back to manual verification", STOP and go to the indicated step.

---

Evidence-based completion verification. Run before claiming any work is done.

## When to Use

- About to say "tests pass", "build succeeds", "bug is fixed", or "feature is complete"
- Before committing, creating a PR, or marking a task as done
- After any code change that should be verified
- When reviewing sub-agent output before trusting it

**Note:** code-forge:impl runs verification automatically. This skill is for general use.

## When NOT to Use

The gate below is built on **running a command and reading its output**. When no such
command exists, this skill has nothing to enforce — do not load it:

| Request | What to do instead |
|---|---|
| Verify a claim, statement, or fact is true | Check the source directly; cite it |
| Verify a document is accurate, complete, or consistent | `spec-forge:audit` / `spec-forge:review` |
| Verify data, numbers, or a spreadsheet reconciles | Do the calculation and show the working |
| Verify a translation, wording, or naming choice | Answer directly — it is a judgment call |

Note the distinction: verifying *that the code does X* is in scope; verifying *that a
sentence is true* is not. When work is partly executable, verify the executable part with
this skill and handle the rest directly — and say which is which.

## Iron Law

**NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

No exceptions. Not "it should work." Not "I just ran it." Not "the agent said it passed."

## The Gate

Every completion claim must pass through this gate — because false claims waste reviewer time and erode trust in automated workflows. A single unverified "tests pass" can mask a regression that reaches production.

```
SCOPE → IDENTIFY → RUN → READ → VERIFY → CLAIM
```

0. **SCOPE** — confirm a command can settle the question. If the claim is about prose,
   facts, data, or a judgment call rather than executable behavior (see §When NOT to Use),
   **STOP**: say so in one line, check the source directly, and do not run this gate. Never
   invent a command just to have something to run.
1. **IDENTIFY** the verification command (test, build, lint, type-check)
2. **RUN** the command fresh (not from memory, not from a previous run)
3. **READ** the complete output (not skimmed, not truncated)
4. **VERIFY** the output matches the claim (zero failures, exit code 0)
5. **ONLY THEN** make the claim

**Example:**
- Before: "I fixed the off-by-one error, tests should pass now."
- Run: `npm test` → Output: `42 passed, 0 failed`
- After: "Off-by-one fix verified — 42 tests pass (0 failures, exit 0)."

## Forbidden Words

These words in a completion claim are red flags — they mean you haven't verified:

- "should work" / "should pass"
- "probably" / "likely"
- "seems to" / "appears to"
- "I believe" / "I think"
- "based on the changes"
- "it worked before"

Replace with evidence: "All 34 tests pass (output: 34 passed, 0 failed, exit code 0)."

If no automated verification exists, state that explicitly: "No automated test covers this — manual verification required: [steps]." This is honest, not hedging.

## Verification Patterns

### Tests
```
Run command → See "X passed, 0 failed" → Claim "all tests pass"
```
NOT: "Tests should pass now" or "I fixed the issue so tests will pass."

### Regression Test
```
Write test → Run (PASS) → Revert fix → Run (MUST FAIL) → Restore fix → Run (PASS)
```
The revert-and-fail step proves the test actually catches the bug.

### Build
```
Run build → See exit code 0, no errors → Claim "build passes"
```

### Requirements Checklist
```
For each requirement:
  [ ] Identified verification method
  [ ] Ran verification
  [ ] Evidence recorded
```
NOT: "Tests pass, so the feature is complete."

### Sub-Agent Output
```
Agent claims success → Check VCS diff → Run tests yourself → Verify changes
```
NEVER trust agent reports without independent verification.

## Common Mistakes

- Trusting memory of a previous test run instead of running fresh
- Reading only the last line of output, missing errors above
- Claiming "build passes" after only running tests (or vice versa)
- Verifying one aspect but claiming completeness for all aspects
- Skipping verification "just this once" because it's a small change
