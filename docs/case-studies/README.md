# Code Forge Skill — Case Studies

This directory contains **regression baselines** for skill behavior. Each file
captures the expected shape of a skill's output on a specific project at a
specific skill revision.

## ⚠️ Not loaded at runtime

Files in this directory are **human-reference only**:

- Nothing in any `skills/*/SKILL.md` `@references` these files.
- No sub-agent prompt points a review agent or fix agent at this directory.
- They are NOT few-shot material. They document metric distributions, not
  reusable finding content.

If you find yourself tempted to `@reference` one of these files from a skill
prompt, STOP — use `skills/*/references/` for prompt material instead, and
keep case studies here purely as regression contracts readable by humans.

## What each case study records

- **Skill version** — commit SHA of the skill at test time.
- **Project profile** — LOC, file count, reference level, module groups.
- **Key metrics** — total findings, severity distribution, density, drop
  counts, sub-agent success rate.
- **What the skill must detect** — abstractly, not as pasteable titles.
- **What the skill must suppress** — abstract noise shapes, not quoted text.
- **Regression thresholds** — band limits that, if crossed, signal the skill
  has degraded.

## How to use for regression

1. Check out the skill commit named in the case study.
2. Run the same skill invocation on the same project.
3. Compare resulting metrics against the thresholds.
4. Crossed thresholds → the skill regressed; investigate recent changes to
   `SKILL.md` / `references/` / prompt wording.

## Why abstract instead of concrete

Concrete findings (*"apcli exec bypasses checkApproval at discovery.ts:289"*)
would anchor the sub-agent's pattern matching to a specific codebase. If the
file is ever loaded into prompt context by accident, concrete findings become
few-shot contamination — the agent may start flagging similar-looking
patterns in unrelated projects. Abstract descriptions ("cross-dispatcher
parity defect in a security-policy path") document the skill's capability
without risking contamination.
