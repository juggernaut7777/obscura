## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2023-10-27 - [Avoid N+1 stat calls with pathlib.Path.glob and os.scandir]
**Learning:** `pathlib.Path.glob()` combined with `.stat().st_size` loop checks causes an N+1 stat calls issue (especially on larger directories with hundreds of files) as it incurs one system call for listing and one additional system call per file matching the glob pattern.
**Action:** Use `os.scandir()` which directly exposes size attributes on Windows and caches system stat calls natively on Linux, resulting in substantial speedups when checking file sizes across an entire directory.
