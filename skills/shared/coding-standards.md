### Coding Standards for Implementation Sub-agents

These standards apply to all code written during task execution. **If the project has a `CLAUDE.md` with team-specific standards, those take precedence over the defaults below.**

Follow the language ecosystem's conventions where they differ from these defaults.

#### Principles (Priority Order)

1. **Readability + Performance** — Code must be understandable by a stranger quickly
2. **Consistency > Preference** — Follow project-wide style uniformly; no personal variations
3. **Explicit > Implicit** — All assumptions, boundaries, and state transitions must be visible in code
4. **Small Units** — Keep functions focused and short; keep files focused on a single responsibility
5. **Testability Built-in** — Core logic should be easy to test; dependencies injectable or mockable
6. **Zero-Tolerance Security** — All user input / external data validated and sanitized

#### Naming Conventions

Follow language ecosystem conventions for casing and style. The key rule is: **names must be intention-revealing**.

**Banned standalone names** (too vague to convey intent when used alone):

| Context | Banned (standalone) | OK when qualified | Why banned alone |
|---|---|---|---|
| Variables | `data`, `temp`, `obj`, `item`, `info`, `val` | `userData`, `formData`, `tempSwap` (algorithm), `cartItem`, `userInfo` | Alone reveals nothing about content |
| Functions | `process()`, `handle()`, `doIt()`, `run()`, `execute()` | `handleClick()`, `processPayment()`, `runMigration()`, `executeQuery()` | Alone reveals nothing about behavior |
| Classes | `Manager`, `Util`, `Helper`, `Base` | `ConnectionManager`, `DateUtil`, `ValidationHelper` | Alone reveals nothing about responsibility |

**Other naming rules:**
- No magic numbers / strings — use named constants (follow language convention for constant casing)
- Function names should describe what the function does
- Class / type names should describe what they represent

#### Function / Method Rules

- **Keep functions focused and short** — a function should do one thing well; if it's getting long, split it
- **Minimize side effects** — isolate I/O and state mutations to boundaries where practical; keep core logic predictable
- **No deep nesting** — use guard clauses (early return) instead of nested `if/else`; prefer flat control flow

#### Comments & Documentation

- **Write comments for:** complex algorithms, performance trade-offs, business rules, counter-intuitive code
- **Never write:** obvious comments like `// get user` or `// increment counter`
- **TODO / HACK / FIXME:** Should include enough context to be actionable later (who, why, when to revisit)

#### Security & Defensive Programming (Non-negotiable)

- **All external input** (HTTP params, form data, file uploads) must be validated before use — prefer schema-based validation over scattered manual checks for complex input
- **Never** concatenate strings into SQL, shell commands, or log messages — use parameterized queries, safe APIs, structured logging
- **Never** hardcode secrets, tokens, or API keys — use environment variables + secret manager
- **Structured logging** for service code: include request context (request ID, trace ID, etc.) in log entries
- **Frontend:** All dynamic content must be escaped / sanitized before rendering; use framework-native safe rendering
