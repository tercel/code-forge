### Skill Execution Contract

**When a SKILL.md is loaded into your context, you MUST immediately begin executing it — do not summarize, do not ask "what should I do now", do not fall back to a manual workflow.** Skills are operational manuals, not reference documents.

The harness message `Successfully loaded skill · N tools allowed` means the SKILL.md content was **injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing their Detailed Steps.

If you find yourself about to say "the skill didn't produce output", "falling back to manual <anything>", or any paraphrase thereof — **STOP**. You have misunderstood how skills work. Go directly to the first executable step indicated by the SKILL.md's per-skill entry line and start.

The first user-visible action of any skill must be either (a) the output of its first executable step, or (b) an `AskUserQuestion` if that step needs disambiguation. **Never an apology. Never a fallback. Never silence.**
