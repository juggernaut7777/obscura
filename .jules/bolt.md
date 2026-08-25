## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2026-06-05 - [Avoid N+1 File Traversal and stat Calls with os.scandir]
**Learning:** Calling `.iterdir()` multiple times on the same directory, or using `.glob()` and then `.stat()` causes redundant file system traversals and N+1 system calls. `os.scandir()` provides a single pass with cached file attributes, which drastically improves directory iteration performance.
**Action:** When filtering files in a directory by multiple conditions (like extension and substring) or when needing file stats, iterate once using `os.scandir()` and group the results.
