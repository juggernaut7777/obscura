## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.
## 2025-02-28 - [Memoize ProductCard in Next.js Storefront]
**Learning:** In the Next.js storefront, list/grid item components like `ProductCard` render multiple times when global state (like `CartContext` toggling) updates parent layouts (like `Home` or `ShopPage`). Since product props are stable data, missing `React.memo()` causes an O(N) re-render bottleneck across the grid.
**Action:** Use `React.memo()` to wrap pure child components in lists or grids that receive stable props to prevent unnecessary re-renders when parent states change.
