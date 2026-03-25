### Project Analysis Protocol

**Purpose:** Build a deep understanding of the project before taking any action. This protocol is referenced by skills that need to understand the codebase (plan, impl, review, fix, debug, tdd). Execute it once at the start; results are reused throughout the skill's workflow.

**When NOT needed:** status, parallel, finish — these are coordination skills that don't analyze code.

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

#### PA.3 Language-Specific Deep Scan

Based on the detected language, apply the appropriate deep scan strategy.

##### Python
| Aspect | What to Scan |
|--------|-------------|
| **Public API** | `__all__` in `__init__.py`, classes without `_` prefix, decorated functions (`@app.route`, `@click.command`) |
| **Logic Complexity** | `if/elif/else` branches, `try/except` blocks, `match/case`, `raise` statements, nested comprehensions |
| **Type System** | Type hints on function signatures, `Protocol` classes (structural typing), `ABC` subclasses (interface contracts), `TypeVar` (generics) |
| **Patterns** | Decorators (analyze what they wrap), context managers (`__enter__/__exit__`), descriptors (`__get__/__set__`), metaclasses |
| **Async** | `async def` functions, `await` chains, `asyncio.gather` concurrency points, `aiohttp` sessions |

##### TypeScript / JavaScript
| Aspect | What to Scan |
|--------|-------------|
| **Public API** | `export` statements in `index.ts`, re-export chains (`export * from`), `default export`, `.d.ts` declarations |
| **Logic Complexity** | `if/else`, `switch/case`, ternary operators, optional chaining (`?.`), nullish coalescing (`??`), `try/catch` chains |
| **Type System** | `interface` definitions, `type` aliases, generic type parameters (`<T extends X>`), discriminated unions, mapped types, utility types |
| **Patterns** | Higher-order functions, closures, React hooks (`useEffect`, `useMemo`), middleware chains, dependency injection (InversifyJS, NestJS `@Injectable`) |
| **Async** | `async/await`, `Promise.all/race/allSettled`, Observable streams (RxJS), event emitter patterns |

##### Go
| Aspect | What to Scan |
|--------|-------------|
| **Public API** | Capitalized identifiers (exported), interface definitions, struct methods (receiver functions) |
| **Logic Complexity** | `if err != nil` chains (count them — Go has verbose error handling), `switch/case`, `select` on channels, goroutine spawn points |
| **Type System** | Interface definitions (implicit satisfaction), struct embedding (composition), type assertions (`x.(Type)`), type switches |
| **Patterns** | Options pattern (`functional options`), middleware chains (`http.Handler` wrapping), table-driven tests, `context.Context` propagation |
| **Concurrency** | `go func()` spawns, `chan` definitions, `sync.Mutex/RWMutex`, `sync.WaitGroup`, `select` statements, `context.WithCancel/Timeout` |

##### Rust
| Aspect | What to Scan |
|--------|-------------|
| **Public API** | Follow mod tree from `lib.rs`. Extract all `pub` items. Track `pub use` re-exports. Distinguish `pub` vs `pub(crate)` vs private. Record `#[derive]` macros that generate behavior. Handle `#[cfg(feature)]` conditional compilation. |
| **Logic Complexity** | `match` arms (exhaustive — each arm is a path). `if let` / `while let` pattern matching. `?` operator chains (early return on error). `unwrap()` / `expect()` calls (panic risk). `unsafe` blocks (high-risk areas). |
| **Type System** | `trait` definitions with required methods and default impls. `impl Trait for Struct` blocks (may be in DIFFERENT files — collect all). Generic type parameters with trait bounds (`T: Handler + Send + 'static`). `where` clauses. Associated types (`type Output`). Lifetime parameters (`'a`, `'static`). |
| **Patterns** | Builder pattern (`FooBuilder`). Newtype pattern (`struct Wrapper(Inner)`). Error enum with `thiserror`/`anyhow`. `From`/`Into` trait impls for type conversion. `Drop` impl for cleanup. `Deref`/`DerefMut` for smart pointer patterns. |
| **Concurrency** | `async fn` + `tokio::spawn` / `async_std::task::spawn`. Channel patterns (`mpsc`, `oneshot`, `broadcast`). `Arc<Mutex<T>>` / `Arc<RwLock<T>>` shared state. `Send`/`Sync` trait bounds. Atomic operations (`AtomicBool`, `AtomicUsize`). |

##### Java
| Aspect | What to Scan |
|--------|-------------|
| **Public API** | `public` classes, interfaces, methods. `@RestController`/`@Service`/`@Repository` annotations. `module-info.java` exports. |
| **Logic Complexity** | `if/else`, `switch` (including pattern matching in Java 17+), `try/catch/finally` chains, `Optional` method chains. |
| **Type System** | `interface` definitions, `abstract class`, generics (`<T extends Comparable<T>>`), sealed classes (Java 17+). |
| **Patterns** | Spring DI (`@Autowired`, `@Inject`), AOP (`@Aspect`), Repository pattern, Service layer, DTO/Entity mapping. |

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

This summary is passed to the skill's subsequent steps — it informs task planning, review focus, debug investigation, and test design.
