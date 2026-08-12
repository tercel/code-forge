# Sub-agent Response Format — Acceptance Reconciliation Agent

This file is **self-contained**. Do NOT read `format-common.md`, `suppression-gates.md`, `call-graph-discipline.md`, or any dimensions file — none of them apply to this agent.

Used by the dedicated acceptance sub-agent in **Step 3G.3** (the Acceptance Gate). This agent has the OPPOSITE polarity from the correctness-review agents: its job is to report ABSENCE of test coverage for required behaviors, not to find bugs in code that exists.

**This agent does NOT produce `METHOD_CHAINS` and does NOT produce `CANDIDATE_INVENTORY`. Its findings do NOT pass through the five Suppression Gates, the Gate-5 evidence-artifact requirement, the speculative-phrase scan, or the observable-downside check.** An uncovered required behavior is the finding; absence is the evidence. Never drop or downgrade an acceptance gap for lack of a reachable-trigger argument or grep artifact.

**Input the agent receives:** `REQUIRED_BEHAVIORS` (the P0/P1 items resolved in Step 3G.1), the list of test files, and the executed-test names + pass/fail status from the fresh run in Step 3G.2.

**Mapping rule:** a behavior is `covered` ONLY when a test (a) exists, (b) executed in this run, (c) passed, and (d) demonstrably exercises the behavior — matched by TC-ID embedded in the test name, or by behavior/assertion when no TC-ID convention exists. Happy-path-only assertions for a behavior that requires boundary/error/negative checks ⇒ `weak`. Skipped / todo / pending / `to-be-automated` ⇒ never `covered`.

```
ACCEPTANCE_RECONCILIATION:
  source: <srs | test-cases | plan | docs | none>
  required_total: <number of P0/P1 behaviors>     # 0 when source == none
  covered: <number>
  uncovered_p0: <number>
  uncovered_p1: <number>
  behaviors:
  - id: <FR-AUTH-001 | TC-AUTH-010 | AC-3 | ...>
    priority: <P0 | P1>
    description: <one line — the required behavior / expected result>
    status: <covered | uncovered | weak>
    test: <test name + file:line that covers it>     # required when status == covered
    note: <for weak: which sub-aspect (boundary/error/negative) is unasserted; for uncovered: omit — absence needs no further evidence>
```

**Verdict computation is done by the orchestrator (Step 3G.4), not the sub-agent.** The orchestrator converts every `uncovered`/`weak` P0 → blocker, every `uncovered`/`weak` P1 → critical, merges these counts into the report, and sets `ACCEPTANCE_GATE = BLOCKED` accordingly.
