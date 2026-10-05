## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2025-02-28 - Avoid Sync FS operations in Next.js API Routes
**Learning:** Using synchronous file system operations (like `fs.readdirSync`, `fs.readFileSync`) inside a loop in Next.js API routes blocks the single-threaded Node.js event loop and significantly degrades performance. Sequential reads are slow. Replacing these with `fs.promises` equivalent methods and utilizing `Promise.all` allows for concurrent I/O operations, improving response time especially when dealing with many files.
**Action:** Use `fs.promises` and concurrent execution (`Promise.all`) in Next.js API routes instead of synchronous `fs` methods to avoid blocking the event loop and improve scalability.
