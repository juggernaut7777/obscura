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

function matchesCategory(product, filter) {
  if (!filter || filter === "all") return true;
  const f = filter.toLowerCase();
  
  if (f === "sale") return (product.comparePrice || 0) > product.price;
  if (f === "new") return Boolean(product.badge && product.badge.toLowerCase().includes("new"));

  // Direct category match (products now have proper categories: Tops, Bottoms, Outerwear, Sets, Accessories, Footwear)
  const cat = (product.category || "").toLowerCase();
  if (cat) {
    if (cat === f) return true;
    if (f === "accessories" && cat === "footwear") return true;
    return false;
  }

  // Fallback ONLY when category is missing: check name/desc
  const name = (product.name || "").toLowerCase();
  const desc = (product.description || "").toLowerCase();
  const text = `${name} ${desc}`;

  if (f === "sets") {
    return Boolean(
      product.isSet ||
      /\b(set|tracksuit|uniform|two-piece)\b/i.test(name)
    );
  }

  if (f === "outerwear") {
    return /\b(jacket|puffer|shell|coat|parka|vest|windbreaker)\b/i.test(text);
  }

  if (f === "bottoms") {
    return /\b(shorts|pants|trousers|sweatpants|jogger|jeans)\b/i.test(text);
  }

  if (f === "tops") {
    return /\b(hoodie|tee|t-shirt|shirt|sweatshirt|knit|crewneck|sweater)\b/i.test(text);
  }

  if (f === "accessories") {
    return /\b(scarf|hat|cap|beanie|bag|wallet|belt|shoe|boot|sneaker|eyewear|sunglasses|jewelry)\b/i.test(text);
  }

  return false;
}

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
    products = products.filter(p => matchesCategory(p, categoryFilter));
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
            <span className="tag-spec">OBSCURA CATALOG</span>
            <h1 className={`heading-display ${styles.title}`} style={{ textTransform: "uppercase", letterSpacing: "0.04em", marginTop: "8px" }}>
              {isWishlistFilter ? 'WISHLIST' : categoryFilter ? (
                categoryFilter === 'sale' ? 'SALE' : 
                categoryFilter === 'new' ? 'NEW ARRIVALS' :
                categoryFilter.toUpperCase()
              ) : 'ALL PRODUCTS'}
            </h1>
            <p className={styles.subtitle}>
              {isWishlistFilter ? 'Your saved items.' : `${products.length} ${products.length === 1 ? 'product' : 'products'} available`}
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
                  prefetch={false}
                  className={`${styles.filterLink} ${(!categoryFilter && cat === 'all') || categoryFilter === cat ? styles.filterActive : ""}`}
                  style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}
                >
                  {cat}
                </Link>
              ))}
              <div className={styles.divider} />
              <Link 
                href="/shop?category=sale"
                prefetch={false}
                className={`${styles.filterLink} ${styles.saleLink} ${categoryFilter === 'sale' ? styles.filterActive : ""}`}
                style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", letterSpacing: "0.14em", textTransform: "uppercase" }}
              >
                SALE
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
                <h3>{DEMO_PRODUCTS.length === 0 ? "ARCHIVE REALLOCATION" : "No products found."}</h3>
                <p>
                  {DEMO_PRODUCTS.length === 0
                    ? "Edition 05 pieces are undergoing editorial capture and curation. New limited allocations arriving shortly."
                    : "We couldn't find any items matching these filters."}
                </p>
                {hasActiveFilters && (
                  <button onClick={clearFilters} className="btn btn-outline">Clear Filters</button>
                )}
              </div>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
