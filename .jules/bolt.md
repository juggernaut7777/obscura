## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2024-05-24 - [Avoid Event Loop Blocking File I/O]
**Learning:** Writing files synchronously inside an `async def` function blocks the asyncio event loop. Using `aiofiles` is one option, but Python 3.9+ includes `asyncio.to_thread` which perfectly resolves this issue without requiring 3rd party dependencies.
**Action:** When working in async contexts (especially Playwright scrapers), encapsulate blocking I/O (like file writes) into a helper function and await it using `asyncio.to_thread()`.
