# Review Dimensions — Intra-Module

Dimensions applied by **per-module sub-agents** (Step 3F.4b / 3P.3b) and, together with `dimensions-cross.md`, by the **fast-path single agent** (3F.4a / 3P.3a) and **GitHub PR mode**.

Scope: D1, D2, D3, D4, D6, D8, D9 — findings rooted in the agent's own `METHOD_CHAINS`, including those discovered through tier-2 inlined cross-module steps. Cross-cutting dimensions (D5, D7, D10-D15) live in `dimensions-cross.md` and are the cross-module agent's responsibility — do NOT apply them here.

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

## Dimension Application Rules

**MANDATORY pre-analysis: `METHOD_CHAINS` must be produced BEFORE any dimension is applied.** See `references/call-graph-discipline.md` and `references/format-per-module.md` §METHOD_CHAINS. All dimensions below are applied against the call graph, not against raw method bodies. D1, D3, and D8 have explicit "source signal from METHOD_CHAINS" paragraphs — consult them when deciding which dimension a finding belongs to.

**MANDATORY post-analysis: every candidate finding from any dimension MUST pass through `references/suppression-gates.md` before being emitted.** The five gates (Reachability, Trust Boundary, Severity Calibration, Quota Avoidance, Factual Verifiability) are not optional — they exist specifically to counter the over-flagging bias produced by exhaustive per-dimension checking.

- **D1–D3 (Tier 1):** Apply to every reviewed scope. Potential merge blockers. **Empty findings are valid** when no real issues exist — do NOT fabricate marginal findings to fill the dimension (Gate 4).
- **D4, D6 (Tier 2):** Apply to every reviewed scope. Should-fix items. **Empty findings are valid.**
- **D8–D9 (Tier 3):** Apply to every reviewed scope. Flag as warnings/suggestions. **Empty findings are valid** — D8/D9 commonly have nothing to say in a clean diff; do not invent observability nits to show effort.

**Quota-avoidance reminder.** Producing a finding because the dimension "feels under-utilized" is the failure mode Gate 4 forbids. The orchestrator does NOT penalize empty dimensions; it DROPS speculative findings and warnings/suggestions without a named downside/benefit (see SKILL.md Step 4F validation steps 2, 4, 5), tracks the drop counts in `drop_share`, and raises the `fabricating` flag when drops exceed 40% of raw output. Quality of findings >> quantity of findings.
