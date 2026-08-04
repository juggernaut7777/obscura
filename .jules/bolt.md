## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2026-08-04 - Eliminate N+1 Web Scraping in Sync Logic
**Learning:** Sequential `await` calls inside loops that hit slow external resources (like headless browsers fetching URLs) cause immense N+1 bottlenecks.
**Action:** Extract the loop body into an async helper function and use `asyncio.gather()` to execute the tasks concurrently.
