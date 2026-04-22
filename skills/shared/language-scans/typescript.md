## TypeScript / JavaScript — Deep Scan Dimensions

| Aspect | What to Scan |
|--------|-------------|
| **Public API** | `export` statements in `index.ts`, re-export chains (`export * from`), `default export`, `.d.ts` declarations |
| **Logic Complexity** | `if/else`, `switch/case`, ternary operators, optional chaining (`?.`), nullish coalescing (`??`), `try/catch` chains |
| **Type System** | `interface` definitions, `type` aliases, generic type parameters (`<T extends X>`), discriminated unions, mapped types, utility types |
| **Patterns** | Higher-order functions, closures, React hooks (`useEffect`, `useMemo`), middleware chains, dependency injection (InversifyJS, NestJS `@Injectable`) |
| **Async** | `async/await`, `Promise.all/race/allSettled`, Observable streams (RxJS), event emitter patterns |
