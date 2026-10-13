## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2025-02-28 - Avoid Sync File Ops in Next.js API Routes and Optimize readdir
**Learning:** Using synchronous file operations (like `fs.readdirSync`, `fs.readFileSync`) in Next.js API routes blocks the single-threaded Node.js event loop, completely freezing concurrent incoming requests. Additionally, calling `fs.stat` on every child element in a loop to check if it's a directory incurs a severe N+1 stat call penalty.
**Action:** Always use `fs.promises` equivalent methods in Next.js API routes. For iterating over directories and checking types, use `fs.promises.readdir(path, { withFileTypes: true })` to get `fs.Dirent` objects directly, preventing the N+1 stat penalty.
