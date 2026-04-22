## Python — Deep Scan Dimensions

| Aspect | What to Scan |
|--------|-------------|
| **Public API** | `__all__` in `__init__.py`, classes without `_` prefix, decorated functions (`@app.route`, `@click.command`) |
| **Logic Complexity** | `if/elif/else` branches, `try/except` blocks, `match/case`, `raise` statements, nested comprehensions |
| **Type System** | Type hints on function signatures, `Protocol` classes (structural typing), `ABC` subclasses (interface contracts), `TypeVar` (generics) |
| **Patterns** | Decorators (analyze what they wrap), context managers (`__enter__/__exit__`), descriptors (`__get__/__set__`), metaclasses |
| **Async** | `async def` functions, `await` chains, `asyncio.gather` concurrency points, `aiohttp` sessions |
