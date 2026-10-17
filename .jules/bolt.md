## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2026-10-17 - Avoid Synchronous File System Calls and N+1 stats in Node
**Learning:** Using synchronous file operations (`fs.readdirSync`, `fs.readFileSync`) in Next.js API routes blocks the main thread. Additionally, using `fs.readdir` without `withFileTypes` leads to N+1 `fs.stat` calls just to determine if entries are directories.
**Action:** Use `fs.promises.readdir` with `withFileTypes: true` and execute iterations with `Promise.all` to keep the API route asynchronous and efficient.
