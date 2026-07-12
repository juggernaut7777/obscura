## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2026-07-12 - [Memoize Expensive React Rendering Work]
**Learning:** In Next.js components like `ShopPage` that rely on `useCart` context, any state change (e.g. toggling cart sidebar) triggers a re-render. Un-memoized expensive operations (like sorting/filtering entire product arrays or extracting unique categories using Sets) will needlessly bottleneck performance.
**Action:** Use `useMemo` to wrap heavy array mapping, filtering, and sorting logic, ensuring they only re-run when their explicit dependencies (like sort order or filter category) change.
