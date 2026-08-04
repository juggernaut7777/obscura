## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2024-05-18 - [Optimize Blocking Loop in VLM Product Sourcer]
**Learning:** In continuous looping scripts (`vlm_product_sourcer.py`), calling `asyncio.run(main())` and `time.sleep()` repeatedly inside a synchronous `while True` loop is inefficient due to event loop setup/teardown overhead and blocking the main thread.
**Action:** Always wrap continuous polling loops in an async coroutine, calling `asyncio.run()` exactly once at the entry point. Use `await asyncio.sleep()` for non-blocking intervals.
