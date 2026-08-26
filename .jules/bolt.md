## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2024-05-18 - Replacing O(N) linear list traversal inside a loop with O(1) dictionary lookup
**Learning:** Calling `next()` in a generator expression to find an item by ID within a list inside a loop creates an $O(N^2)$ bottleneck that heavily impacts performance on larger lists (e.g., product catalog generation or accumulation).
**Action:** Always precompute an ID-to-object dictionary using dictionary comprehension (e.g., `lookup = {p["id"]: p for p in list}`) before the loop and use `.get()` to achieve $O(1)$ lookups instead.
