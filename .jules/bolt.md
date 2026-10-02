## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2025-03-01 - Avoid Sync I/O in Node API Routes
**Learning:** Using synchronous file operations (`fs.readdirSync`, `fs.readFileSync`) in Next.js API routes blocks the single-threaded Node.js event loop, significantly degrading concurrent performance.
**Action:** Always use asynchronous methods (`fs.promises.readdir`, `fs.promises.readFile`) combined with `Promise.all` for parallel execution in API routes.
