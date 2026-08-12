# Review Dimensions — Cross-Module & Architecture

Dimensions applied by the **cross-module aggregation agent** (Step 3F.5 / 3P.4) and, together with `dimensions-intra.md`, by the **fast-path single agent** (3F.4a / 3P.3a) and **GitHub PR mode**.

Scope: D5, D7, D10-D15 — dimensions that need the full picture across module boundaries. Intra-module dimensions (D1, D2, D3, D4, D6, D8, D9) live in `dimensions-intra.md` and are already covered by the per-module agents — do NOT re-apply them here.

## Tier 2 — Should-Fix (★★★★☆)

### D5: Architecture & Design

Does the change fit the project's architectural conventions?

Check items:
- **Layer boundaries:** Respects existing architectural layers (controller/service/repo, MVC, hexagonal, etc.)
- **Dependency direction:** No circular dependencies, lower layers don't depend on higher layers
- **SOLID principles:** Single responsibility, open-closed, interface segregation violations
- **Coupling:** New code not tightly coupled to implementation details of other modules
- **Abstraction level:** Not introducing a parallel system alongside an existing one
- **API surface:** Public interfaces are clean, minimal, consistent, and well-defined
- **Module cohesion:** Related functionality grouped together; no God Class / God Function
- **New abstractions justified:** If new patterns/frameworks/base classes are introduced, are they warranted?

### D15: Simplification & Anti-Bloat

Does this change keep the codebase lean, or does it pile on redundancy and dead weight? This dimension is **mandatory for every review** — it is the primary defense against incremental bloat from skill-driven (spec-forge / code-forge / apcore-skills) workflows that bias toward "add new" over "reuse existing".

**Mindset:** Treat every new file, function, class, abstraction, parameter, config knob, and dependency as a liability that must justify itself against what already exists. The default answer is "reuse or extend", not "create new".

Check items:
- **Reuse over new:** Was an equivalent or near-equivalent function/class/utility already present in the project? Grep for similar names, similar signatures, similar string literals — if the new code reimplements something that exists, flag it as `critical` (must merge into the existing one) and do not let it slip through as duplication.
- **Dead code from this change:** New functions/classes/exports/types/constants that are defined but never referenced anywhere in the diff or in the rest of the codebase. Flag at `warning` minimum; `critical` if they form a parallel unused subsystem.
- **Pre-existing dead code touched by this change:** If the change modifies a file that contains already-dead symbols (unused imports, unreachable branches, commented-out blocks, never-called helpers, stale `TODO` placeholders), flag them — the review pass is the right time to clean them out, not "later".
- **Speculative abstraction:** Base classes, interfaces, plugin systems, generics, factories, or "extension points" introduced for hypothetical future needs that have exactly one (or zero) current callers. Flag at `warning` **only when `evidence` concretely demonstrates the simpler replacement** — quote the single current call site AND sketch the 5–15-line concrete form that would replace it. Without that demonstration the finding is speculative ("someone might later want to swap this out") and MUST be dropped — the orchestrator's Step 4F warning-downside check will drop it anyway; pre-empt by not emitting. Extensions that exist for interface conformance at an architectural boundary (adapter pattern, dependency injection seam) are NOT bloat even with zero current second callers.
- **Premature parameterization:** Function parameters, config keys, environment variables, or feature flags added "in case someone needs to tune this" but with only one call site passing the default. Flag at `warning` **only when `evidence` enumerates every call site AND shows every site passes the same value**. If call sites diverge (even across tests), the parameter is justified — drop. A parameter with exactly one production call site but exercised by tests with varied values is also justified.
- **Wrapper / passthrough functions:** New functions whose body is a single call to another function with the same arguments, or that only rename fields without adding logic. Flag at `warning` **only when `evidence` shows the wrapper adds no value** — no different error handling, no different logging, no type-narrowing, no testability gain, no interface conformance need. Wrappers at architectural boundaries (adapter / port / DI seam) are NOT bloat — drop the finding for those. Thin wrappers that exist purely to make a call site readable are also acceptable; flag only when the wrapper is pure noise with no reader benefit.
- **Parallel implementations:** A new module that does roughly what an existing module already does, but slightly differently. Most common failure mode of skill-driven feature work. Flag at `critical` — propose merging.
- **Copy-paste blocks:** Two or more code blocks (≥ 5 lines) that are structurally identical or differ only in literals. Flag at `warning` and propose extraction — but only if the extracted form is genuinely simpler, not a forced abstraction.
- **Scope creep beyond the plan:** Files, modules, or features added that are not required by the feature's `plan.md` / spec / task list. Flag at `warning`; `critical` if they introduce new dependencies or new public API.
- **Backward-compat shims for code that was never released:** `_legacy_*` aliases, deprecated re-exports, "removed" comments, renamed `_unused` variables for code that exists only on this branch. Flag at `warning` — delete instead.
- **Defensive code for impossible states:** Validation, null checks, try/except, or fallbacks guarding scenarios that the type system or upstream invariants already prevent. Flag at `suggestion`. **Do NOT apply this check to external-input paths** — iteration over plugin return values, subscript into deserialized config, reads from the network, etc., are genuinely external and can be malformed regardless of upstream invariants. Missing guards on those paths are a **D1 finding, not a D15 one** (and subject to §Finding Suppression Gate Gate 2 — only flag when the source is genuinely external per the project's threat model). Check `METHOD_CHAINS[].external_inputs[]` to distinguish: `guarded: false` on an external-input path AND source crosses a trust boundary is D1 territory; `guarded: true` on a type-system-guaranteed-non-external path is D15 territory; `guarded: false` on an internal/trusted source is **dropped per Gate 2**, not flagged in either dimension.
- **Comment / docstring bloat:** Comments restating what the code obviously does, auto-generated docstrings on trivial helpers, file-level banner comments with no information. Flag at `suggestion`.
- **Configuration knobs nobody asked for:** New entries in `config.{json,yaml,toml}`, new CLI flags, new env vars not driven by an explicit requirement. Flag at `warning`.
- **Dependency creep:** A new third-party dependency pulled in to do something that 10 lines of project code (or an existing dependency) could do. Flag at `warning`; `critical` if the dependency is large, unmaintained, or duplicates an existing one.

**Sub-agent execution requirements for D15:**
1. **Grep before flagging additions.** Before claiming "new function `foo` is fine", run a project-wide search for similar names and signatures. The sub-agent must demonstrate it looked for existing equivalents.
2. **Read import graphs.** For every new top-level symbol in the diff, verify at least one caller exists outside the file that defines it. Symbols with zero external callers go on the dead-code list.
3. **Compare against `plan.md` / spec.** Anything in the diff that is not traceable to a planned task or acceptance criterion is scope creep — list it.
4. **Net-LOC sanity check.** If the change adds significantly more lines than the plan estimated, and the excess is not test code, surface this in the report as a signal of likely bloat.

**Severity guidance for D15:**
- `critical` — duplicate implementation of existing functionality; large parallel subsystem; new dependency that overlaps an existing one
- `warning` — unused new symbols; speculative abstractions; passthrough wrappers; copy-paste blocks; unjustified new config/flags
- `suggestion` — defensive code for impossible states; comment bloat; minor stylistic redundancy

D15 is **always applied** regardless of project type, language, or reference level. It is the only dimension whose explicit job is to push back on the additive bias of automated planning skills.

---

### D7: Test Coverage & Verifiability

Are critical paths tested? Are tests meaningful?

**Relationship to the Acceptance Gate (SKILL.md §Acceptance Gate).** D7 is the *qualitative* judgment — are the tests that exist meaningful, independent, deterministic, asserting behavior not implementation? It is subject to the suppression gates like every other dimension. D7 does NOT verify that every required behavior from the spec has a passing test — that *mechanical reconciliation* (required P0/P1 behavior → named passing test, absence = blocker) is the Acceptance Gate's job, which runs separately in Step 3G, actually executes the suite, and is NOT subject to the suppression gates. The two are complementary: the Acceptance Gate proves the required behaviors are tested at all; D7 judges whether those (and other) tests are any good. Keep applying D7 normally.

Check items:
- **Coverage of critical paths:** Core business logic, state transitions, and data transformations have tests
- **Happy path:** Normal/expected flow is tested
- **Sad path:** Error conditions, invalid inputs, failure scenarios are tested
- **Edge cases:** Boundary values, empty inputs, concurrent access, large inputs
- **Test independence:** Tests don't depend on execution order or shared mutable state
- **Determinism:** No flaky tests relying on timing, network, or random data without seeding
- **Meaningful assertions:** Tests assert behavior, not implementation; not just "no error thrown"
- **Test naming:** Test names describe the scenario and expected behavior
- **Mock appropriateness:** External dependencies mocked; internal logic not over-mocked
- **Missing test files:** Source modules without any corresponding test coverage

## Tier 3 — Recommended Fix (★★★☆☆)

### D10: Standards & Conventions

Does the code follow team and project conventions?

Check items:
- **Lint compliance:** Code passes project linter configuration
- **File/directory structure:** Follows project's established organization patterns
- **Import ordering:** Follows project convention for import grouping/ordering
- **Dependency management:** New dependencies declared properly, version pinned, justified
- **Naming conventions:** Files, classes, functions follow project naming patterns (camelCase, snake_case, etc.)
- **Configuration:** New config via environment variables or config files, not hardcoded
- **No surprise technology:** New frameworks, libraries, or patterns introduced without team discussion

## Tier 4 — Nice-to-Have / Track as Tech Debt (★★☆☆☆ / ★☆☆☆☆)

### D11: Backward Compatibility & Ops-Friendliness

Will this change break existing consumers or complicate deployment?

Check items:
- **API contract:** Existing API fields/endpoints not removed or semantically changed without versioning
- **Database schema:** Column renames, type changes, or drops have migration + backward-compat strategy
- **Configuration changes:** New required config keys have defaults or migration docs
- **Cache/queue keys:** Key format changes won't corrupt existing cached data
- **Enum/constant changes:** Value semantics preserved; new values don't break existing consumers
- **Rollback safety:** Can this change be rolled back without data loss or corruption?
- **Feature flags / gradual rollout:** High-risk changes gated behind feature flags

### D12: Maintainability & Tech Debt

Does this change leave the codebase better or worse?

Check items:
- **Copy-paste debt:** Large duplicated blocks that should be extracted
- **Deep inheritance:** Inheritance depth > 3 levels; prefer composition
- **Magic configuration:** Behavior controlled by non-obvious environment variables or config
- **Over-engineering:** Abstractions, extension points, or patterns for hypothetical future needs
- **Under-engineering:** Quick hacks that will clearly need rework soon (TODO/FIXME/HACK comments)
- **Coupling to internals:** Depending on internal implementation details of libraries or other modules

### D13: Dependencies & Supply Chain Security

Are new or updated dependencies safe and justified?

Check items:
- **Known CVEs:** Dependencies scanned for known vulnerabilities
- **Version pinning:** Versions locked (lockfile present and updated); not using `latest` or `*`
- **Minimal footprint:** Not pulling in a large library for a small utility
- **Maintenance status:** Dependency actively maintained, not abandoned/archived
- **License compatibility:** License compatible with project requirements
- **Transitive risk:** Major transitive dependencies checked for known issues

### D14: Accessibility / i18n (Frontend & Mobile Only)

Is the UI usable by all users? _(Skip this dimension for backend-only projects.)_

Check items:
- **Semantic HTML:** Proper use of heading levels, landmarks, form labels
- **ARIA attributes:** Interactive elements have appropriate `aria-label`, `role`, states
- **Keyboard navigation:** All interactive elements reachable and operable via keyboard
- **Color contrast:** Text meets WCAG AA contrast ratio (4.5:1 for normal text)
- **Hardcoded strings:** User-visible text uses i18n/l10n framework, not hardcoded
- **RTL support:** Layout not broken in right-to-left languages (if applicable)
- **Screen reader:** Dynamic content changes announced; focus management correct

## Dimension Application Rules

**MANDATORY pre-analysis: the per-module `METHOD_CHAINS` handed to this agent are the analysis substrate.** See `references/call-graph-discipline.md` and `references/format-cross-module.md`. Dimensions are applied against the aggregated call graph, not against raw method bodies. D15 has an explicit "source signal from METHOD_CHAINS" paragraph — consult it when deciding which dimension a finding belongs to.

**MANDATORY post-analysis: every candidate finding from any dimension MUST pass through `references/suppression-gates.md` before being emitted.** The five gates (Reachability, Trust Boundary, Severity Calibration, Quota Avoidance, Factual Verifiability) are not optional — they exist specifically to counter the over-flagging bias produced by exhaustive per-dimension checking.

- **D5, D7, D15 (Tier 2):** Apply to every reviewed scope. Should-fix items. **Empty findings are valid.**
- **D10 (Tier 3):** Apply to every reviewed scope. Flag as warnings/suggestions. **Empty findings are valid** — do not invent standards nits to show effort.
- **D11–D13 (Tier 4):** Apply to every reviewed scope. Expect mostly suggestions. **Empty findings are valid and common.**
- **D14 (Accessibility/i18n):** Apply ONLY if `project_type` is `"frontend"` or `"fullstack"`.
- **D15 (Simplification & Anti-Bloat):** Apply to every reviewed scope, in every mode and on every project type. This dimension exists specifically to counter the additive bias of automated planning skills (spec-forge / code-forge / apcore-skills) and must never be skipped, even for small diffs. Empty D15 findings are still valid, BUT the agent must demonstrate it actively grep'd for duplicates and read import graphs (see D15 execution requirements above) — silent emptiness is suspicious; demonstrated emptiness is correct.

**Quota-avoidance reminder.** Producing a finding because the dimension "feels under-utilized" is the failure mode Gate 4 forbids. The orchestrator does NOT penalize empty dimensions; it DROPS speculative findings and warnings/suggestions without a named downside/benefit (see SKILL.md Step 4F validation steps 2, 4, 5), tracks the drop counts in `drop_share`, and raises the `fabricating` flag when drops exceed 40% of raw output. Quality of findings >> quantity of findings.
