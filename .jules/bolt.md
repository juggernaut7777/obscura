## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2024-09-03 - Optimize Directory Iteration
**Learning:** `Path.iterdir()` paired with `is_dir()` or `is_file()` incurs N+1 `stat()` calls, making it noticeably slow on large directories compared to `os.scandir()`, which caches file attributes.
**Action:** Replace list comprehensions like `[d for d in Path.iterdir() if d.is_dir()]` with `[Path(e.path) for e in os.scandir(Path) if e.is_dir()]` in highly-traversed paths.
