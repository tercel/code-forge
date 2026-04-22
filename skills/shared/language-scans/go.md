## Go — Deep Scan Dimensions

| Aspect | What to Scan |
|--------|-------------|
| **Public API** | Capitalized identifiers (exported), interface definitions, struct methods (receiver functions) |
| **Logic Complexity** | `if err != nil` chains (count them — Go has verbose error handling), `switch/case`, `select` on channels, goroutine spawn points |
| **Type System** | Interface definitions (implicit satisfaction), struct embedding (composition), type assertions (`x.(Type)`), type switches |
| **Patterns** | Options pattern (`functional options`), middleware chains (`http.Handler` wrapping), table-driven tests, `context.Context` propagation |
| **Concurrency** | `go func()` spawns, `chan` definitions, `sync.Mutex/RWMutex`, `sync.WaitGroup`, `select` statements, `context.WithCancel/Timeout` |
