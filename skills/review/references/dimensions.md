# Review Dimensions Reference

The following dimensions are used in both Feature Mode and Project Mode reviews. They are ordered by priority tier.

## Tier 1 — Must-Fix Before Merge (★★★★★)

### D1: Functional Correctness & Business Logic

Does the code actually implement what it should? This is the highest-priority dimension.

Check items:
- **Requirements fulfillment:** Does the code implement the specified behavior correctly?
- **Boundary conditions:** Off-by-one errors, empty collections, zero/negative values, max values, null/undefined
- **Concurrency & race conditions:** Shared mutable state, missing locks/synchronization, TOCTOU bugs
- **Idempotency:** Are operations safe to retry? Are duplicate requests handled?
- **State transitions:** Are all states reachable? Are invalid transitions prevented?
- **Data consistency:** Transactions boundaries, partial failure handling, eventual consistency gaps
- **Type correctness:** Type coercion surprises, implicit conversions, generic type safety
- **Edge cases in business rules:** Negative amounts, timezone handling, leap years, Unicode, locale-specific logic

### D2: Security Vulnerabilities

Does the code introduce any security risk?

Check items:
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

- **D1–D3 (Tier 1):** Always apply. These are potential merge blockers.
- **D4–D7 (Tier 2):** Always apply. These are should-fix items.
- **D8–D10 (Tier 3):** Always apply. Flag as warnings/suggestions.
- **D11–D13 (Tier 4):** Always apply but expect mostly suggestions.
- **D14 (Accessibility/i18n):** Apply ONLY if `project_type` is `"frontend"` or `"fullstack"`.
