### Project Analysis Protocol

**Purpose:** Build a deep understanding of the project before taking any action. This protocol is referenced by skills that need to understand the codebase (plan, impl, review, fix, debug, tdd). Execute it once at the start; results are reused throughout the skill's workflow.

**When NOT needed:** status, parallel, finish — these are coordination skills that don't analyze code.

---

#### PA.0 Fast-path: collect raw facts first

Before the manual scans, run the facts collector once — it gathers the
enumeration signals (language mix, build files, dependency names, detected
frameworks, test files + framework + command, source-tree top level,
entrypoints) in a single pass instead of many Grep/Glob round-trips. Resolve
`<cf_scripts>` once (see *Locating the script layer* in the configuration step —
it lives in the install, not the project), then:

```bash
python3 "<cf_scripts>/cf-scan.py"
```

Use its JSON as the starting inventory for PA.1, PA.2.1, and PA.5. It is a
**facts collector, not an analyst** — architecture pattern (PA.2.2), dependency
direction (PA.2.3), call graph and data flow (PA.4), and risk assessment (PA.7)
are still your job; verify the collector's guesses before relying on them. If
`python3` is unavailable, perform the scans below entirely by hand.

---

#### PA.1 Project Profile Detection

Determine what kind of project this is. Scan for framework signatures in build/config files:

```
Use Grep on: package.json, pyproject.toml, Cargo.toml, go.mod, build.gradle, pom.xml, requirements.txt, composer.json
```

| Signal | Profile |
|--------|---------|
| HTTP framework (Express, FastAPI, Spring Boot, Gin, NestJS, Koa, Hono, Actix-web, Axum, Rocket, Flask, Django, Rails, etc.) + route handlers | **Web API** |
| CLI framework (Click, Cobra, Commander, clap, argparse with subcommands, Yargs, etc.) + command handlers | **CLI Tool** |
| Frontend framework (React, Vue, Svelte, Angular, Solid, etc.) + component files | **Frontend App** |
| LLM/AI framework (LangChain, Vercel AI SDK, AutoGen, CrewAI, etc.) + tool definitions | **AI Agent** |
| Pipeline/ETL framework (Airflow, Prefect, dbt, Luigi, etc.) + pipeline definitions | **Data Pipeline** |
| Published package with exported functions/classes, no routes/commands/components | **Function Library** |
| Client/SDK wrapper with connection management, API methods | **SDK / Client Library** |
| Multiple profiles detected (e.g., API + CLI) | **Hybrid** — note which parts match which profile |

Also determine:
- **Primary language**: from file extensions + build config
- **Has database**: ORM/migration files detected? (`prisma/`, `alembic/`, `migrations/`, `diesel.toml`, `knex`, etc.)
- **Has auth**: auth middleware, JWT/OAuth imports, permission decorators?
- **Has external APIs**: HTTP client usage (axios, reqwest, net/http, etc.) calling third-party services?
- **Has message queue**: RabbitMQ, Kafka, Redis pub/sub, NATS imports?
- **Has background jobs**: Celery, BullMQ, Sidekiq, Tokio tasks?

**Output**: "Project Profile: **{type}** ({language}). Database: {yes/no}. Auth: {yes/no}. External APIs: {yes/no}."

#### PA.2 Architecture Analysis

Understand how the project is structured — layers, modules, boundaries.

**PA.2.0 Caching (optional)**

PA.2's module tree and architecture pattern change on a monthly cadence, while the code they describe changes every commit. Cache the slow, stable half — never the fast half.

Cache file: `<project_root>/.code-forge/arch-cache.json`. `.code-forge/` is already gitignored (see the configuration step). **Never write this into `output_dir` / `planning/`** — a derived artifact under version control produces merge conflicts and false "the docs disagree with the code" review signals.

Fingerprint (cheap, whole-cache invalidation — no incremental staleness tracking):

```bash
{ git ls-files 'package.json' '*/package.json' '*/project.json' \
      'pyproject.toml' '*/pyproject.toml' 'Cargo.toml' '*/Cargo.toml' 'go.mod' '*/go.mod';
  git ls-files | sed 's|/[^/]*$||' | sort -u; } | shasum -a 256 | cut -c1-16
```

Manifest set plus directory tree. If the fingerprint matches, reuse the cache; otherwise recompute PA.2 in full and rewrite it. Do not attempt incremental invalidation — the added complexity reintroduces exactly the staleness risk the cache is supposed to be safe from.

| Cached | Not cached |
|---|---|
| `architecture_pattern` (PA.2.2), module tree (PA.2.1), package/workspace boundaries | import edges (PA.2.3), call graph and data flow (PA.4), test status (PA.5) |

The right-hand column is excluded on purpose. Those change every commit, and **a stale dependency graph is worse than no graph**: absent a graph, grouping falls back to directory splitting — a known, predictable degradation; with a stale one, it produces a confidently wrong partition whose cost (chains cut across agents, evidence split, both false positives and false negatives) is invisible in the output.

**PA.2.1 Module Structure**

Scan the source directory to map the module tree:

| Language | How to Map |
|----------|-----------|
| Python | `src/` or top-level package → `__init__.py` imports → subpackages |
| TypeScript | `src/` → `index.ts` exports → barrel files → module directories |
| Go | Root package + `internal/` + `cmd/` → package imports |
| Rust | `src/lib.rs` → `mod` declarations → recursive module files. Follow EVERY `mod foo;` to `src/foo.rs` or `src/foo/mod.rs`. Track `pub use` re-exports. |
| Java | `src/main/java/` → package hierarchy → class files |

**PA.2.2 Layer Pattern Recognition**

Identify the architectural pattern by examining module names and import directions:

| Pattern | Signals | Layer Structure |
|---------|---------|-----------------|
| **MVC** | `controllers/`, `models/`, `views/` or `templates/` | Controller → Model → View |
| **Clean/Hexagonal** | `domain/`, `ports/`, `adapters/`, `use_cases/` or `application/` | Adapters → Use Cases → Domain |
| **Layered API** | `routes/` or `handlers/`, `services/`, `repositories/` or `dal/` | Route → Service → Repository → DB |
| **Component-based** | `components/`, `hooks/`, `stores/`, `utils/` | Components → Hooks/Stores → Utils |
| **Plugin/Extension** | `plugins/`, `extensions/`, `middleware/` | Core → Plugin Interface → Plugins |
| **Monorepo** | `packages/` or `apps/` with separate build configs | Multiple sub-projects |

**PA.2.3 Dependency Direction**

Verify dependency direction is correct (no circular deps, lower layers don't import upper):

```
For each source file:
  Extract import/use/require statements
  Map: which module imports which
  Check: does any lower-layer module import from upper layer? (violation)
```

**Establish the baseline contract before checking.** Inferring the expected direction from directory names and then checking the code against that inference is near-circular — the rule is derived from the same layout it is meant to police, so a codebase that is *consistently* wrong reads as correct. Look for a declared contract first (**read-only** — these express human intent; never generate or overwrite them):

- `ARCHITECTURE.md`, `docs/architecture.md`, `docs/adr/`, `docs/design/`
- Machine-enforced boundaries: `import/no-restricted-paths` in ESLint config; `@nx/enforce-module-boundaries` with `tags` in `nx.json` / `project.json`; `import-linter` contracts in `setup.cfg` / `pyproject.toml`; Go `internal/` placement; Rust workspace member visibility

Record `architecture_contract = {source: <path> | "inferred", rules: [...]}`.

The divergence between a **declared** contract and the actual edges is a first-class D5 finding, and it is worth strictly more than anything the inferred baseline can yield:

> `docs/architecture.md` declares repositories must not import services — 12 such edges exist (cite each as `file:line`)

**Severity anchoring:** a violated *declared* rule is a broken promise and may reach `critical`. A violated *inferred* rule is capped at `warning` — nobody promised it. State which baseline was used in the finding; a reader cannot judge the finding without it.

#### PA.3 Language-Specific Deep Scan

Based on the primary language detected in PA.1, **read the single matching language-scan reference** for the dimensions to inspect. This keeps the main context lean — only the relevant language's check-list is loaded.

| Detected language | Read this file |
|-------------------|----------------|
| Python | `shared/language-scans/python.md` |
| TypeScript / JavaScript | `shared/language-scans/typescript.md` |
| Go | `shared/language-scans/go.md` |
| Rust | `shared/language-scans/rust.md` |
| Java | `shared/language-scans/java.md` |

For a **Hybrid** project (multiple primary languages), read each applicable file. For a language not listed (Ruby, PHP, C#, Kotlin, Swift, etc.), apply the generic public-API / logic-complexity / type-system / patterns / concurrency framing using the above tables as templates and note the language in the Project Context Summary.

#### PA.4 Relationship Mapping

Map how units interact with each other. This determines where integration tests are needed and where bugs propagate.

**PA.4.1 Call Graph**

For each public function/method, trace what it calls:
```
createUser (route)
  → validateInput (service)
  → hashPassword (util)
  → userRepository.save (repository)
  → sendWelcomeEmail (event handler)
```

**PA.4.2 Data Flow**

Trace how data transforms as it flows through the system:
```
HTTP Request body (JSON)
  → parsed to CreateUserDTO
  → validated (field constraints)
  → mapped to User entity
  → persisted to database
  → mapped to UserResponse
  → serialized to JSON response
```

**PA.4.3 Trait/Interface Implementations** (especially important for Go/Rust)

Map which concrete types implement which abstract interfaces:
```
trait Handler:
  impl Handler for AuthHandler
  impl Handler for LoggingHandler
  impl Handler for RateLimitHandler
```

**PA.4.4 Event/Message Flow**

Map event publishers to subscribers:
```
UserCreatedEvent:
  published by: UserService.create()
  consumed by: EmailService.sendWelcome(), AnalyticsService.trackSignup()
```

#### PA.5 Existing Test Assessment

Understand what testing already exists:

1. **Find test files**: `**/*.test.*`, `**/*.spec.*`, `**/__tests__/**`, `**/test_*`, `**/tests/**`, `*_test.go`, `*_test.rs`
2. **Detect test framework**: Jest, pytest, Go test, cargo test, JUnit, Vitest, etc.
3. **Detect test runner command**: Check `package.json` scripts, `Makefile`, `Cargo.toml`, CI config
4. **Map coverage**: For each test file, identify which source units are tested
5. **Identify test patterns**: unit tests, integration tests, E2E tests, fixtures, mocks, test helpers

#### PA.6 Completeness Verification

After scanning, verify the analysis is thorough:

| Check | How | Threshold |
|-------|-----|-----------|
| File coverage | Source files scanned / total source files | ≥ 90% |
| Module tree (Rust) | `mod` declarations followed / total `mod` declarations | 100% |
| Re-export tracking (Rust/TS) | `pub use` / `export *` resolved / total | 100% |
| Unit density | Extracted units / scanned files | 2-10 per file (flag outliers) |
| Import coverage | Import statements traced / total imports | ≥ 80% |

If any check fails, re-scan the missed areas before proceeding.

#### PA.7 Output: Project Context Summary

Produce a structured summary that downstream steps can reference:

```
## Project Context

**Profile**: Web API (Express + TypeScript)
**Language**: TypeScript 5.x
**Database**: PostgreSQL via Prisma
**Auth**: JWT with passport middleware
**Architecture**: Layered API (routes → services → repositories)
**Arch contract**: declared — docs/architecture.md (or: inferred — findings capped at `warning`)

### Module Map
  src/routes/     — 8 route files, 24 endpoints
  src/services/   — 6 service classes
  src/repositories/ — 4 repository classes
  src/middleware/  — 3 middleware (auth, logging, error-handler)
  src/utils/      — 5 utility modules

### Key Relationships
  routes → services (1:1 mapping)
  services → repositories (1:1 or 1:N)
  middleware → all routes (cross-cutting)

### Test Status
  Framework: Jest + Supertest
  Command: npm test
  Coverage: 34/52 units have tests (65%)
  Gaps: repositories/ (0% coverage), middleware/error-handler (no tests)

### Risk Areas
  - repositories/ — no tests, DB-touching, high impact
  - middleware/auth — security-critical, only 1 test
  - services/payment — external API integration, complex error handling
```

This summary is passed to the skill's subsequent steps — it informs task planning, review focus, debug investigation, and test design. `architecture_pattern` and `architecture_contract` are load-bearing for review's module grouping (SKILL.md §3F.3.2): the pattern picks the split axis, and the contract sets the severity ceiling for dependency-direction findings. Pass both forward rather than letting a downstream step re-derive them from directory names.
