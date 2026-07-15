## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2025-03-05 - [Memoize List Item Components with React.memo]
**Learning:** In the Next.js storefront, global context state updates (like toggling `CartContext`) trigger re-renders in parent page layouts. Without memoization, this causes O(N) re-renders of all children, such as `ProductCard` components in a grid or list, even if their props haven't changed. This is a common performance bottleneck in React applications using global context for UI state.
**Action:** Wrap list/grid item components (e.g., `ProductCard`) that receive stable props in `React.memo()` to prevent unnecessary re-renders when parent components update.
