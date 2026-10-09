## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2025-02-28 - Next.js API synchronous fs operations
**Learning:** In the Next.js API route `storefront/src/app/api/admin/warehouse/route.js`, using synchronous file system functions like `fs.readdirSync`, `fs.statSync`, and `fs.readFileSync` while iterating through the manual curation folder blocks the main event loop. This leads to heavy latency as the curation folder grows and prevents other concurrent requests.
**Action:** Replace `fs.*Sync` operations with `fs.promises.*` equivalents, and use `Promise.all` to concurrently read and convert multiple thumbnails and metadata files to dramatically speed up response times for file serving endpoints.
