## Rust — Deep Scan Dimensions

| Aspect | What to Scan |
|--------|-------------|
| **Public API** | Follow mod tree from `lib.rs`. Extract all `pub` items. Track `pub use` re-exports. Distinguish `pub` vs `pub(crate)` vs private. Record `#[derive]` macros that generate behavior. Handle `#[cfg(feature)]` conditional compilation. |
| **Logic Complexity** | `match` arms (exhaustive — each arm is a path). `if let` / `while let` pattern matching. `?` operator chains (early return on error). `unwrap()` / `expect()` calls (panic risk). `unsafe` blocks (high-risk areas). |
| **Type System** | `trait` definitions with required methods and default impls. `impl Trait for Struct` blocks (may be in DIFFERENT files — collect all). Generic type parameters with trait bounds (`T: Handler + Send + 'static`). `where` clauses. Associated types (`type Output`). Lifetime parameters (`'a`, `'static`). |
| **Patterns** | Builder pattern (`FooBuilder`). Newtype pattern (`struct Wrapper(Inner)`). Error enum with `thiserror`/`anyhow`. `From`/`Into` trait impls for type conversion. `Drop` impl for cleanup. `Deref`/`DerefMut` for smart pointer patterns. |
| **Concurrency** | `async fn` + `tokio::spawn` / `async_std::task::spawn`. Channel patterns (`mpsc`, `oneshot`, `broadcast`). `Arc<Mutex<T>>` / `Arc<RwLock<T>>` shared state. `Send`/`Sync` trait bounds. Atomic operations (`AtomicBool`, `AtomicUsize`). |
