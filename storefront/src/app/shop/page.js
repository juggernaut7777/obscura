"use client";
import { use } from "react";
import { useState } from "react";
import Link from "next/link";
import { useCart } from "@/context/CartContext";
import { useWishlist } from "@/context/WishlistContext";
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
  const isWishlistFilter = unwrappedParams?.wishlist === "true";

  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem } = useCart();
  const { wishlist } = useWishlist();
  const [sort, setSort] = useState("new");
  const [selectedColor, setSelectedColor] = useState("");
  const [selectedSize, setSelectedSize] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Filter products
  let products = [...DEMO_PRODUCTS];

  if (isWishlistFilter) {
    products = products.filter((p) => wishlist.includes(p.id));
  } else if (categoryFilter && categoryFilter !== "all") {
    if (categoryFilter === "sale") {
      products = products.filter(p => p.comparePrice > 0);
    } else if (categoryFilter === "new") {
      products = products.filter(p => p.badge && p.badge.toLowerCase().includes('new'));
    } else {
      products = products.filter(p => p.category.toLowerCase() === categoryFilter.toLowerCase());
    }
  }

  if (selectedColor) {
    products = products.filter(p => p.colors?.some(c => c.name.toLowerCase() === selectedColor.toLowerCase()));
  }

  if (selectedSize) {
    products = products.filter(p => {
      if (p.stock_status) {
        return Object.entries(p.stock_status).some(([key, inStock]) => key.endsWith(`-${selectedSize}`) && inStock);
      }
      return p.sizes?.includes(selectedSize);
    });
  }

  // Sort products
  if (sort === "price-low") products.sort((a, b) => a.price - b.price);
  if (sort === "price-high") products.sort((a, b) => b.price - a.price);
  
  // Brand Categories (full brand taxonomy)
  const categories = ["all", "outerwear", "tops", "bottoms", "sets", "accessories"];
  const allColors = Array.from(new Set(DEMO_PRODUCTS.flatMap(p => p.colors?.map(c => c.name) || []))).filter(Boolean);
  const allSizes = ["S", "M", "L", "XL", "2XL"];

  const clearFilters = () => {
    setSelectedColor("");
    setSelectedSize("");
    setSort("new");
  };

  const hasActiveFilters = selectedColor || selectedSize || sort !== "new";

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
              {isWishlistFilter ? 'Your Saved Wishlist' : categoryFilter ? (
                categoryFilter === 'sale' ? 'Archive Sale' : 
                categoryFilter === 'new' ? 'New Arrivals' :
                categoryFilter.charAt(0).toUpperCase() + categoryFilter.slice(1)
              ) : 'The Complete Collection'}
            </h1>
            <p className={styles.subtitle}>
              {isWishlistFilter ? 'Your personal curation of saved pieces.' : 'Every piece in our collection is designed with intention. Browse the full catalog.'}
            </p>
          </div>
        </header>

        <section className={`container ${styles.shopSection}`}>
          {/* Controls Bar */}
          <div className={styles.controls}>
            {/* Category Filter Links */}
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

            {/* Right Controls: Filter Toggle + Sort */}
            <div className={styles.rightControls}>
              <button 
                onClick={() => setShowFilters(!showFilters)}
                className={`${styles.filterToggleBtn} ${showFilters || hasActiveFilters ? styles.filterToggleActive : ""}`}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/>
                </svg>
                <span>Filter &amp; Refine</span>
                {hasActiveFilters && <span className={styles.filterDot} />}
              </button>

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
          </div>

          {/* Collapsible Advanced Filters */}
          {showFilters && (
            <div className={`${styles.advancedFilters} animate-fade-in`}>
              {allColors.length > 0 && (
                <div className={styles.filterGroup}>
                  <span className={styles.filterGroupLabel}>Color</span>
                  <div className={styles.chipGroup}>
                    {allColors.map(color => (
                      <button
                        key={color}
                        onClick={() => setSelectedColor(selectedColor === color ? "" : color)}
                        className={`${styles.chip} ${selectedColor === color ? styles.chipActive : ""}`}
                      >
                        {color}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              <div className={styles.filterGroup}>
                <span className={styles.filterGroupLabel}>Size</span>
                <div className={styles.chipGroup}>
                  {allSizes.map(size => (
                    <button
                      key={size}
                      onClick={() => setSelectedSize(selectedSize === size ? "" : size)}
                      className={`${styles.chip} ${selectedSize === size ? styles.chipActive : ""}`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>

              {hasActiveFilters && (
                <button onClick={clearFilters} className={styles.clearBtn}>
                  Clear Filters
                </button>
              )}
            </div>
          )}

          {/* Grid */}
          <div className={styles.grid}>
            {products.length > 0 ? (
              products.map((product, i) => (
                <ProductCard key={product.id} product={product} index={i} />
              ))
            ) : (
              <div className={styles.emptyState}>
                <h3>No products found.</h3>
                <p>We couldn't find any items matching these filters.</p>
                <button onClick={clearFilters} className="btn btn-outline">Clear Filters</button>
              </div>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
