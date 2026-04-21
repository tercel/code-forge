# Review Dimensions Reference

The following dimensions are used in both Feature Mode and Project Mode reviews. They are ordered by priority tier.

## Tier 1 — Must-Fix Before Merge (★★★★★)

### D1: Functional Correctness & Business Logic

Does the code actually implement what it should? This is the highest-priority dimension.

**D1 must be applied against the `METHOD_CHAINS` call graph produced by pre-analysis, not against the surface method body.** A method can pass surface reading yet fail D1 because its chain omits expected work — that is exactly the failure mode `METHOD_CHAINS` exists to expose.

Check items:
- **Requirements fulfillment:** Does the code implement the specified behavior correctly?
- **Chain completeness (sourced from METHOD_CHAINS):** For every entry with `chain_completeness != matches_purpose`, emit a finding. A `partial` chain — the method's stated purpose implies steps the chain omits (e.g., public method `register` documented to validate-id-format + resolve-deps + insert-into-index + emit-event, but chain only does insert + emit — validate and resolve are missing) — is `critical`. A `suspicious` chain — the chain contradicts the method's name/signature/promise (e.g., method named `discover` returns a count but no state mutation updates the main index peers would update; method named `register` silently overwrites without raising on duplicate when the signature implies strict mode) — is `blocker`. Quote the `gaps[]` list in the description.
- **Defensive gap on external inputs (sourced from METHOD_CHAINS `external_inputs`):** For every external-input path where `guarded: false` AND the source is **genuinely external per §Finding Suppression Gate Gate 2**, emit a `critical` finding. **"Genuinely external" means crossing a trust boundary the project recognizes:** user-facing HTTP/RPC/WebSocket payload, plugin callback return value from a third-party plugin, network response, deserialized blob from outside the repo, file uploaded by an untrusted user, cross-tenant data. **NOT genuinely external:** the project's own source files scanned by its own dev tools, hard-coded constants, repo-committed config files the developer authored, type-checked function arguments inside one trusted process. For internal/trusted sources, drop the finding (or flag at `suggestion` if the project's threat model in README/SECURITY.md explicitly elevates the source). Examples of valid critical findings: `for entry of externalList` with no null/array-check on data from an HTTP request body; `dict["key"]` subscript on a deserialized JWT payload with no `KeyError` / `in` guard; `json.loads(req.body).foo` with no schema validation. This is D1's territory, NOT D15's "defensive code for impossible states" — D15 flags guards against *impossible* states (upstream invariant or type system already prevents); D1 flags missing guards against *reachable, externally-supplied, malformed-able* states. **When in doubt for a clearly internal dev tool, drop per Gate 2.**
- **Boundary conditions:** Off-by-one errors, empty collections, zero/negative values, max values, null/undefined
- **Concurrency & race conditions:** Shared mutable state, missing locks/synchronization, TOCTOU bugs
- **Idempotency:** Are operations safe to retry? Are duplicate requests handled?
- **State transitions:** Are all states reachable? Are invalid transitions prevented?
- **Data consistency:** Transactions boundaries, partial failure handling, eventual consistency gaps
- **Type correctness:** Type coercion surprises, implicit conversions, generic type safety
- **Edge cases in business rules:** Negative amounts, timezone handling, leap years, Unicode, locale-specific logic

### D2: Security Vulnerabilities

Does the code introduce any security risk?

**Trust-boundary preface (mandatory — applies to every D2 check below).** Before flagging any D2 finding, evaluate the project's threat model and the data source's trust boundary per §Finding Suppression Gate Gate 2:

- **For projects that ARE security-sensitive** (auth, crypto, payments, multi-tenant SaaS, anything handling secrets of parties other than the developer, anything published as a service to untrusted users): apply D2 fully against any external-facing input.
- **For developer tools / code generators / linters / build scripts that read the developer's own files in the developer's own environment**: drop D2 findings whose attack scenario requires the developer to author malicious input against their own tool. The threat model does not include "the developer attacks themselves". Flag only when the tool ingests data from a genuinely untrusted source (downloaded plugins from a public registry, fetched config from a network endpoint, file uploaded by an end user).
- **When in doubt**, classify the project as a developer tool (the more restrictive case) and drop the finding. The orchestrator's Suppression-Gate validator will auto-downgrade D2 findings against internal/trusted sources for `library` / `cli` / `unknown` project types — pre-empt this by not emitting them in the first place. (Note: `frontend`/`backend`/`fullstack` are NOT auto-downgraded by the orchestrator; if you flag those types' D2 findings, they will surface as-is for human review.)

Check items (each subject to the trust-boundary preface):
- **Input validation:** All external input (HTTP params, form data, file uploads, user-provided env vars) must be validated before use — prefer schema-based validation over scattered manual checks for complex input
- **Injection:** SQL injection (string concatenation), command injection, LDAP injection, template injection — never concatenate strings into SQL, shell commands, or log messages; use parameterized queries and safe APIs
- **XSS:** Reflected, stored, DOM-based — unescaped user content in HTML/JS; dynamic frontend content must use framework-native safe rendering
- **Authentication & authorization:** Missing auth checks, privilege escalation, insecure session management
- **Secrets management:** Hardcoded credentials, API keys in code, secrets in logs, `.env` committed — use environment variables + secret manager
- **CSRF / SSRF:** Missing tokens, unvalidated redirect URLs, internal network access
- **Deserialization:** Unsafe deserialization of untrusted data (pickle, Java serialization, JSON.parse with eval)
- **Cryptography:** Weak algorithms (MD5/SHA1 for passwords), ECB mode, predictable random, custom crypto
- **Path traversal:** Unsanitized file paths from user input
- **Log forging / information disclosure:** Sensitive data in logs, verbose error messages to users; structured logging with request context recommended for service code
- **Dependency vulnerabilities:** Known CVEs in direct or transitive dependencies

### D3: Resource Management & Lifecycle

Are all acquired resources properly released? This is especially critical for long-running services.

**Source signal from METHOD_CHAINS:** for every `kind: mutate` step whose detail is a resource acquisition (`lock.acquire`, `open(...)`, `connect(...)`, `setInterval`, `addEventListener`, `spawn`, `start_transaction`), the same chain must contain the matching release step on every exit path. Missing release on the error path is the most common D3 finding and is visible in the chain as an acquire step without a corresponding release before the `raise` / `return Err` steps.

Check items:
- **Event listeners:** `addEventListener` without `removeEventListener` on cleanup
- **Timers:** `setInterval`/`setTimeout` without `clearInterval`/`clearTimeout`
- **Subscriptions:** Observables, pub/sub, WebSocket connections not unsubscribed on teardown
- **File handles / DB connections:** Opened but not closed, missing `finally`/`defer`/`using`/`with`
- **Goroutine / thread / fiber leaks:** Spawned without termination condition or cancellation
- **Memory:** Unbounded caches/maps, closures capturing large scopes, circular references preventing GC
- **Stream / iterator:** Not consumed or not closed, backpressure not handled
- **Framework lifecycle:** React `useEffect` cleanup, Angular `OnDestroy`, Vue `onUnmounted`, iOS `deinit`

## Tier 2 — Should-Fix (★★★★☆)

### D4: Code Quality & Readability

Is the code clear, maintainable, and following project conventions?

Check items:
- **Naming:** Variables, functions, classes use descriptive, intention-revealing names; no vague standalone names (`data`, `temp`, `obj`, `item`, `info`, `val`, `process()`, `handle()`, `doIt()`, `Manager`, `Util`, `Helper`) — qualified forms like `userData`, `handleClick()`, `ConnectionManager` are fine; follow language ecosystem conventions
- **Magic values:** No unexplained literals — use named constants
- **Function length:** Functions > 50 lines should be scrutinized; > 100 lines likely needs splitting (defer to project `CLAUDE.md` for team-specific thresholds)
- **Side effects:** I/O and state mutations should be isolated to boundaries where practical; keep core logic predictable and testable
- **Control flow:** Prefer guard clauses (early return) over deeply nested `if/else`
- **DRY:** No copy-pasted logic blocks; shared behavior extracted appropriately
- **Dead code:** No unused functions, unreachable branches, commented-out code, unused imports
- **Comments quality:** Present only where logic isn't self-evident (complex algorithms, performance trade-offs, business rules, counter-intuitive code); no obvious/redundant comments; `TODO` / `HACK` / `FIXME` should include enough context to be actionable later
- **Code structure:** Appropriate abstractions, no unnecessary complexity or premature optimization
- **Consistent style:** Follows project's existing patterns for formatting, file organization, module structure

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

### D6: Performance & Efficiency

Are there obvious performance problems on hot paths?

Check items:
- **N+1 queries:** Database queries inside loops
- **Missing indexes:** Frequent queries on unindexed columns
- **Unnecessary allocations:** Creating objects inside tight loops, large object copies on hot paths
- **Blocking in async context:** Synchronous I/O in async code, `await` in loops when `Promise.all` is appropriate
- **Lock granularity:** Oversized critical sections, lock contention on hot paths
- **Cache misuse:** Cache stampede / thundering herd, unbounded cache growth, no TTL
- **Algorithmic complexity:** O(n²) or worse where O(n log n) or O(n) is feasible
- **Payload size:** Fetching all columns when only a few needed, unbounded result sets, no pagination
- **Frontend:** Unnecessary re-renders, missing memoization, layout thrashing, large bundle imports

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

### D8: Error Handling & Robustness

Are errors properly caught, classified, reported, and recovered from?

**Source signal from METHOD_CHAINS:** cross-reference the `raise` steps in every chain against the method's documented error contract (from docstring, plan.md, or spec). A chain that raises an error type not documented is a D8 finding (missing error contract). A chain whose `external_inputs[]` path can throw but which has no `try/except` upstream in the graph is a D8 robustness finding. A chain that catches broadly (`except Exception` leaf) and emits no `raise` step is a **swallowed exception** — always flag at `critical` minimum.

Check items:
- **Swallowed exceptions:** Catch blocks that silently ignore errors (empty catch, catch-and-log-only for critical ops)
- **Over-broad catch:** Catching `Exception` / `Error` / `object` instead of specific types
- **Error propagation:** Errors from downstream services/APIs properly surfaced or wrapped
- **User-facing errors:** Error messages are user-friendly, no stack traces or internal details leaked
- **Timeout handling:** Network calls, DB queries, external APIs have timeouts configured
- **Retry logic:** Retries have backoff, jitter, and max-retry limits; not infinite retry loops
- **Fallback / degradation:** Critical paths have fallback behavior when dependencies fail
- **Promise / async errors:** Unhandled promise rejections, missing `.catch()`, missing error boundaries (React)

### D9: Observability (Logging / Metrics / Tracing)

Can you debug and monitor this code in production?

Check items:
- **Structured logging:** Key business operations emit structured logs with context (user ID, request ID, operation)
- **Log levels:** Appropriate use of debug/info/warn/error levels
- **Error logging:** Exceptions logged with stack traces and context; not swallowed silently
- **Sensitive data in logs:** No passwords, tokens, PII, or credit card numbers in log output
- **Request tracing:** Trace ID / correlation ID propagated across service boundaries
- **Business metrics:** Key business events have counters/gauges (orders placed, payments processed, errors)
- **Health/readiness signals:** Service exposes health checks if applicable
- **Alertability:** Can an on-call engineer understand and act on the logs/metrics this code produces?

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

**MANDATORY pre-analysis: `METHOD_CHAINS` must be produced BEFORE any dimension is applied.** See the parent SKILL.md §Call-Graph Discipline and `sub-agent-format.md` §METHOD_CHAINS. All dimensions below are applied against the call graph, not against raw method bodies. D1, D3, D8, and D15 have explicit "source signal from METHOD_CHAINS" paragraphs — consult them when deciding which dimension a finding belongs to.

**MANDATORY post-analysis: every candidate finding from any dimension MUST pass through §Finding Suppression Gate (parent SKILL.md) before being emitted.** The four gates (Reachability, Trust Boundary, Severity Calibration, Quota Avoidance) are not optional — they exist specifically to counter the over-flagging bias produced by exhaustive per-dimension checking.

- **D1–D3 (Tier 1):** Apply to every reviewed scope. Potential merge blockers. **Empty findings are valid** when no real issues exist — do NOT fabricate marginal findings to fill the dimension (Gate 4).
- **D4–D7, D15 (Tier 2):** Apply to every reviewed scope. Should-fix items. **Empty findings are valid.**
- **D8–D10 (Tier 3):** Apply to every reviewed scope. Flag as warnings/suggestions. **Empty findings are valid** — D8/D9/D10 commonly have nothing to say in a clean diff; do not invent observability/standards nits to show effort.
- **D11–D13 (Tier 4):** Apply to every reviewed scope. Expect mostly suggestions. **Empty findings are valid and common.**
- **D14 (Accessibility/i18n):** Apply ONLY if `project_type` is `"frontend"` or `"fullstack"`.
- **D15 (Simplification & Anti-Bloat):** Apply to every reviewed scope, in every mode and on every project type. This dimension exists specifically to counter the additive bias of automated planning skills (spec-forge / code-forge / apcore-skills) and must never be skipped, even for small diffs. Empty D15 findings are still valid, BUT the agent must demonstrate it actively grep'd for duplicates and read import graphs (see D15 execution requirements above) — silent emptiness is suspicious; demonstrated emptiness is correct.

**Quota-avoidance reminder.** Producing a finding because the dimension "feels under-utilized" is the failure mode §Finding Suppression Gate Gate 4 forbids. The orchestrator does NOT penalize empty dimensions; it DROPS speculative findings and warnings/suggestions without a named downside/benefit (see Step 4F validation steps 2, 4, 5), tracks the drop counts in `drop_share`, and raises the `fabricating` flag when drops exceed 40% of raw output. Quality of findings >> quantity of findings.
