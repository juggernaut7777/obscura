## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2025-02-28 - Avoid Synchronous fs in Next.js APIs
**Learning:** Using synchronous fs operations like `fs.readdirSync` and `fs.readFileSync` in Next.js API routes blocks the single-threaded Node.js event loop, freezing the application. Additionally, using `fs.readdirSync` followed by `fs.statSync` inside a loop creates an N+1 performance bottleneck.
**Action:** Always use `fs.promises` equivalent methods in API routes. Use `fs.promises.readdir(path, { withFileTypes: true })` to avoid N+1 stat calls when iterating directories.
