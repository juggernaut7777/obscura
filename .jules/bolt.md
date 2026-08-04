## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2026-08-04 - Concurrency in Asynchronous Sourcing
**Learning:** Checking product stock statuses one by one using a `for` loop executing an `await` statement created an O(N) bottleneck, taking N times longer per product. Because `asyncio` is used, the time cost can be minimized.
**Action:** Replaced sequential `for` loops that `await` I/O or network tasks with an asynchronous local function wrapper, calling `asyncio.gather` for concurrent execution, and utilizing an `asyncio.Semaphore` to protect system resources.
