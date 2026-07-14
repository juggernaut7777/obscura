## 2025-02-28 - [Avoid N+1 Stat Calls with os.scandir]
**Learning:** Using `pathlib.Path.iterdir()` combined with `.stat().st_mtime` to sort files by modification time leads to N+1 system calls (one for reading the directory and N for stat). `os.scandir()` caches file attributes, making it significantly faster for this operation (~50% faster in a directory of 100 files). This is a codebase-specific performance pattern to watch for, especially when dealing with many files.
**Action:** Use `os.scandir()` instead of `iterdir()` when iterating over directories and immediately accessing file attributes like `st_mtime`.

## 2023-10-27 - [Prevent O(N) Re-renders with React.memo in Grids]
**Learning:** In the storefront Next.js app, parent page layouts (like `Home` and `ShopPage`) are subscribed to global `CartContext`. Toggling the cart sidebar triggers a re-render of the parent, which cascades down to every `ProductCard` in the product grid, causing O(N) unnecessary renders.
**Action:** Use `React.memo()` to wrap list/grid item components (e.g., `ProductCard`) that receive stable props. This ensures they only re-render when their specific data changes, not when unrelated global UI state updates.
