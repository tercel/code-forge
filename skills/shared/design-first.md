### Design Discipline: Design-First Over Patch-First

These rules apply to **every** code change — new features, adjustments, bug fixes, refactors. They are the upstream defense against the incremental bloat that monotonically grows codebases under skill-driven development. The downstream defenses (review D15, finish simplification gate, audit D9) exist precisely because patch-first development was the default; this file fixes the upstream behavior.

**The Iron Law of Code Changes:**

> **Read first. Design second. Patch only as a last resort.**

#### The Four Rules

1. **Read first — understand before you touch.**
   Before writing a single line of production code, fully understand the relevant subsystem: its data flow, abstractions, naming, existing utilities, current test scaffolding. You must be able to explain how the code works *today* before you may change it. Use `Read`, `Grep`, and import-graph traversal liberally. If you cannot articulate the existing design, you are not ready to modify it.

2. **Then consider the optimal design.**
   Ask: "Given what already exists, what is the cleanest shape this change can take?" Bias toward refactoring the existing structure to absorb the new requirement cleanly. Do **not** default to bolting on a new branch, wrapper, parameter, parallel module, `_v2` file, or feature flag. The first instinct should always be: "Can the existing structure absorb this change with a small refactor?"

3. **Public interfaces are stable.**
   The "optimal design" is constrained: external/public interfaces (APIs, exported symbols, CLI flags, file formats, database schemas, protocol contracts) must remain compatible unless the change explicitly authorizes a break. Internal restructuring is fair game; surface changes are not. When in doubt, treat any symbol exported from the package boundary as public.

4. **Patch development is the fallback, not the default.**
   Adding `if new_case:` branches, new flags, new wrapper classes, parallel modules, or `_v2` files to avoid touching existing code is the wrong instinct unless the optimal design genuinely requires it. Patch development is acceptable only when (a) the existing design is already well-shaped for the change and a patch is the cleanest expression of it, OR (b) refactoring is too risky and the user has been informed of the trade-off.

#### Pre-Code Checklist (run mentally before every change)

Before writing or modifying production code, answer all four questions in order:

1. **What exists?** Briefly state what the relevant subsystem currently does, where its abstractions live, and which existing functions/classes/utilities are adjacent to the change.
2. **What is the optimal shape?** Describe the cleanest design that absorbs the new requirement, *assuming* you can refactor existing internal structure freely (but keeping public interfaces stable).
3. **Refactor or patch?** Compare option A (refactor existing code to absorb the change) against option B (add new code alongside existing code). Pick A unless A is clearly worse on cost, risk, or clarity.
4. **What stays stable?** Enumerate which interfaces/symbols/files this change MUST NOT alter to preserve compatibility.

If you cannot answer all four, you have not read enough — go back to rule 1.

#### Anti-Patterns to Avoid

These are signals that you are patching instead of designing:

- **The `if new_case:` branch.** Adding a new branch to an existing function for a new code path, when the right shape might be a polymorphic dispatch, a strategy object, or a refactor of the function's parameters.
- **The wrapper class.** Wrapping an existing class to add one method, when extending the existing class (or replacing one of its methods) would be cleaner.
- **The parallel module.** Creating `auth_v2.py` next to `auth.py` because `auth.py` is "scary". Either refactor `auth.py` properly or stay inside it; never both.
- **The opt-in feature flag.** Adding `enable_new_thing=False` to thread the new behavior through, when the new behavior should simply replace the old behavior.
- **The new utility file.** Creating `utils/new_helper.py` for a function that should live next to its single caller, or that duplicates something already in `utils/`.
- **The "just expose this internal thing".** Promoting a previously-internal symbol to public so the new code can use it, instead of moving the new code to where it can use the symbol while it stays internal.
- **The premature interface.** Introducing a new abstract base class, interface, protocol, or trait for a single concrete implementation, "in case someone needs to extend it later".
- **The bug-fix epicycle.** Fixing a bug by adding a special case that compensates for the bug, instead of fixing the underlying logic. The new special case becomes the next bug.

#### When Patch Development IS Acceptable

Design-first does not mean refactor-always. Patching is the right call when:

- The existing structure is already well-shaped, and the change is genuinely additive (e.g., a new endpoint that fits cleanly into an existing router, a new field that fits cleanly into an existing schema).
- The refactor would touch code outside the current task's scope and cannot be safely tested in isolation. In this case, surface the trade-off to the user and let them decide between patch-now-and-refactor-later versus expand-scope-now.
- The change is a one-character or one-line fix where the cost of refactoring exceeds the benefit (e.g., fixing a typo in a string literal, changing a constant).
- The user has explicitly asked for a minimal patch and not a refactor.

In all four cases, you must have actually read the surrounding code and considered the alternative. "I didn't bother to look" is never an excuse.

#### How This Interacts with TDD

TDD's Red-Green-Refactor cycle includes refactor as a first-class step — design-first reinforces it. When you finish the GREEN step:

- **Refactor is not optional.** Look at the code you just wrote in the context of the surrounding subsystem. Did the GREEN step push you toward a patch when a small refactor would have produced a cleaner whole? If so, refactor now while the test is green.
- **Refactor stays inside the test's safety net.** All existing tests must remain green throughout. If a refactor breaks tests other than the one you just made green, you have either found a hidden bug or your refactor went out of scope — investigate before continuing.

#### How This Interacts with the Reuse Report

If a `reuse_report` (from code-forge:plan Step 4.5) is available for the current feature, treat it as the authoritative answer to "what exists?" — you do not need to re-discover what it already lists. Components marked `REUSE` must be used, components marked `EXTEND` must be modified (not shadowed), and the `NEW_CODE_BUDGET` is your upper bound for new files. The reuse report is the upstream artifact; design-first is the operational discipline that uses it.

#### How This Interacts With Code Review

The code-forge:review skill's D15 dimension (Simplification & Anti-Bloat) is the *detector* for design-first violations. If you follow design-first, D15 should find nothing on your changes. If D15 flags duplicate implementations, speculative abstractions, wrapper functions, or scope creep on your code, it means design-first was skipped — go back and reconsider rather than arguing the warning.
