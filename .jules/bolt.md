## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2024-10-24 - N+1 Stat Calls in Directory Traversals
**Learning:** In heavily I/O-bound modules like `autonomous_manager.py`, using `Path.iterdir()` coupled with `.is_dir()` checks causes significant N+1 system call overhead because each file existence check triggers a new `stat` call.
**Action:** When scanning large output or curation directories, prefer `os.scandir()` which returns `DirEntry` objects that cache file attributes (like `is_dir()`), drastically reducing filesystem overhead.
