## Java — Deep Scan Dimensions

| Aspect | What to Scan |
|--------|-------------|
| **Public API** | `public` classes, interfaces, methods. `@RestController`/`@Service`/`@Repository` annotations. `module-info.java` exports. |
| **Logic Complexity** | `if/else`, `switch` (including pattern matching in Java 17+), `try/catch/finally` chains, `Optional` method chains. |
| **Type System** | `interface` definitions, `abstract class`, generics (`<T extends Comparable<T>>`), sealed classes (Java 17+). |
| **Patterns** | Spring DI (`@Autowired`, `@Inject`), AOP (`@Aspect`), Repository pattern, Service layer, DTO/Entity mapping. |
