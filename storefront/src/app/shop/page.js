"use client";
import { use, useState, useMemo } from "react";
import Link from "next/link";
import { useCart } from "@/context/CartContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import ProductCard from "@/components/ProductCard";
import { DEMO_PRODUCTS } from "@/data/products";
import styles from "./page.module.css";

export default function ShopPage({ searchParams }) {
  // Unwrap searchParams using React.use()
  const unwrappedParams = use(searchParams);
  const categoryFilter = unwrappedParams?.category;

  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem } = useCart();
  const [sort, setSort] = useState("new");

  // Get unique categories for filter
  const categories = useMemo(() => ["all", ...Array.from(new Set(DEMO_PRODUCTS.map(p => p.category.toLowerCase())))], []);

  // Filter and sort products
  const products = useMemo(() => {
    let result = [...DEMO_PRODUCTS];
    if (categoryFilter && categoryFilter !== "all") {
      if (categoryFilter === "sale") {
        result = result.filter(p => p.comparePrice > 0);
      } else if (categoryFilter === "new") {
        result = result.filter(p => p.badge === "New");
      } else {
        result = result.filter(p => p.category.toLowerCase() === categoryFilter.toLowerCase());
      }
    }

    // Sort products
    if (sort === "price-low") result.sort((a, b) => a.price - b.price);
    if (sort === "price-high") result.sort((a, b) => b.price - a.price);

    return result;
  }, [categoryFilter, sort]);

  return (
    <>
      <Header cartCount={cartItems.length} onCartClick={() => setCartOpen(true)} />
      <CartSidebar
        isOpen={cartOpen}
        onClose={() => setCartOpen(false)}
        items={cartItems}
        onUpdateQty={updateQty}
        onRemove={removeItem}
      />

      <main className={styles.main}>
        {/* Shop Header */}
        <header className={styles.header}>
          <div className="container">
            <h1 className={`heading-display ${styles.title}`}>
              {categoryFilter ? (
                categoryFilter === 'sale' ? 'Archive Sale' : 
                categoryFilter === 'new' ? 'New Arrivals' :
                categoryFilter.charAt(0).toUpperCase() + categoryFilter.slice(1)
              ) : 'The Complete Collection'}
            </h1>
            <p className={styles.subtitle}>
              Every piece in our collection is designed with intention.
              Browse the full catalog.
            </p>
          </div>
        </header>

        <section className={`container ${styles.shopSection}`}>
          {/* Controls Bar */}
          <div className={styles.controls}>
            {/* Filter Links */}
            <div className={styles.filters}>
              {categories.map(cat => (
                <Link 
                  key={cat} 
                  href={cat === 'all' ? '/shop' : `/shop?category=${cat}`}
                  className={`${styles.filterLink} ${(!categoryFilter && cat === 'all') || categoryFilter === cat ? styles.filterActive : ""}`}
                >
                  {cat}
                </Link>
              ))}
              <div className={styles.divider} />
              <Link 
                href="/shop?category=sale"
                className={`${styles.filterLink} ${styles.saleLink} ${categoryFilter === 'sale' ? styles.filterActive : ""}`}
              >
                Sale
              </Link>
            </div>

            {/* Sort Dropdown */}
            <div className={styles.sort}>
              <span className={styles.sortLabel}>Sort by</span>
              <select 
                className={styles.sortSelect} 
                value={sort} 
                onChange={(e) => setSort(e.target.value)}
                aria-label="Sort products"
              >
                <option value="new">Newest</option>
                <option value="price-low">Price: Low to High</option>
                <option value="price-high">Price: High to Low</option>
              </select>
            </div>
          </div>

          {/* Grid */}
          <div className={styles.grid}>
            {products.length > 0 ? (
              products.map((product, i) => (
                <ProductCard key={product.id} product={product} index={i} />
              ))
            ) : (
              <div className={styles.emptyState}>
                <h3>No products found.</h3>
                <p>We couldn't find any items matching this category.</p>
                <Link href="/shop" className="btn btn-outline">Clear Filters</Link>
              </div>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
