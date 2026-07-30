## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2025-02-28 - [Consolidating Multi-Pass Directory Scans]
**Learning:** Iterating over a directory multiple times using `Path.iterdir()` or `Path.glob()` (e.g., first to find JSONs, then to find PNGs, then JPEGs) incurs significant I/O overhead. In `storefront_uploader.py`, replacing three separate `iterdir()` passes with a single `os.scandir()` loop that categorizes files on the fly yielded a ~6x speedup during benchmarking, avoiding redundant system calls.
**Action:** When extracting different types of files from the same directory, use a single `os.scandir()` pass and categorize files inside the loop, rather than doing multiple passes.
