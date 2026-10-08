## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2025-02-28 - Non-blocking async file I/O in API routes
**Learning:** Synchronous file system operations (`fs.readdirSync`, `fs.readFileSync`) in Next.js API routes block the single-threaded event loop and degrade performance under load. Concurrent asynchronous file reading using `fs.promises` and `Promise.all` prevents event loop blocking while significantly improving concurrency speed.
**Action:** Always use `fs.promises` (or equivalent async methods) for file system operations in API routes to keep the event loop non-blocking.
