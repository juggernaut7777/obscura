"use client";
import { useState } from "react";
import Link from "next/link";
import { useCart } from "@/context/CartContext";
import Header from "@/components/Header";
import ProductCard from "@/components/ProductCard";
import CartSidebar from "@/components/CartSidebar";
import Footer from "@/components/Footer";
import { DEMO_PRODUCTS, COLLECTIONS } from "@/data/products";
import styles from "./page.module.css";

export default function Home() {
  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem } = useCart();
  const [newsletterSubmitted, setNewsletterSubmitted] = useState(false);
  const [newsletterEmail, setNewsletterEmail] = useState("");

  const featured = DEMO_PRODUCTS.slice(0, 4);
  const newArrivals = DEMO_PRODUCTS.slice(0, 8);

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

      <main>
        {/* ═══ HERO SECTION ═══ */}
        <section className={styles.hero}>
          <div className={styles.heroOverlay} />
          <div className={styles.heroGrain} />

          <div className={`container ${styles.heroContent}`}>
            <span className={`${styles.heroLabel} animate-fade-in-up`}>
              New Season — Curated Drops
            </span>
            <h1 className={`${styles.heroTitle} animate-fade-in-up delay-2`}>
              Where <em>East</em> meets edge
            </h1>
            <p className={`${styles.heroSub} animate-fade-in-up delay-3`}>
              Deconstructed luxury. Chinese designer craft. Streetwear precision.
              Every piece sourced from the underground.
            </p>
            <div className={`${styles.heroCTA} animate-fade-in-up delay-4`}>
              <Link href="/shop" className="btn btn-primary">Shop the Drop</Link>
              <Link href="/lookbook" className="btn btn-outline">Lookbook →</Link>
            </div>
          </div>

          {/* Scroll indicator */}
          <div className={styles.scrollIndicator}>
            <div className={styles.scrollLine} />
          </div>
        </section>

        {/* ═══ MARQUEE ═══ */}
        <div className={styles.marquee}>
          <div className={styles.marqueeTrack}>
            {[...Array(3)].map((_, i) => (
            <span key={i} className={styles.marqueeText}>
                FREE SHIPPING ON ORDERS OVER $200 &nbsp;✦&nbsp; 
                NEW DROPS EVERY FRIDAY &nbsp;✦&nbsp; 
                SOURCED FROM THE UNDERGROUND &nbsp;✦&nbsp;
              </span>
            ))}
          </div>
        </div>

        {/* ═══ FEATURED PRODUCTS ═══ */}
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <div>
                <span className="text-caption">Curated Selection</span>
                <h2 className={`heading-display ${styles.sectionTitle}`}>Featured Pieces</h2>
              </div>
              <Link href="/shop" className="btn btn-ghost">
                View All →
              </Link>
            </div>

            <div className={styles.productGrid}>
              {featured.map((product, i) => (
                <ProductCard key={product.id} product={product} index={i} />
              ))}
            </div>
          </div>
        </section>

        {/* ═══ EDITORIAL BANNER ═══ */}
        <section className={styles.editorial}>
          <div className={`container ${styles.editorialInner}`}>
            <div className={styles.editorialText}>
              <span className="text-caption">The Philosophy</span>
              <h2 className={`heading-display ${styles.editorialTitle}`}>
                Not fast fashion.<br />Not slow fashion.<br />Our fashion.
              </h2>
              <p className={styles.editorialBody}>
                We source from Chinese ateliers and underground designers
                who build with intention — deconstructed silhouettes, 
                engineered fabrics, and pieces you won&apos;t find on any
                high street. Every drop is limited. Every restock is rare.
              </p>
              <Link href="/shop" className="btn btn-outline">Our Story</Link>
            </div>
            <div className={styles.editorialImage}>
              <img
                src="/images/editorial_hero.jpg"
                alt="OBSCURA Luxury Fashion Editorial"
                loading="lazy"
              />
            </div>
          </div>
        </section>

        {/* ═══ COLLECTIONS ═══ */}
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <div>
                <span className="text-caption">Explore</span>
                <h2 className={`heading-display ${styles.sectionTitle}`}>Collections</h2>
              </div>
            </div>

            <div className={styles.collectionsGrid}>
              {COLLECTIONS.map((col, i) => (
                <Link
                  key={col.id}
                  href="/shop"
                  className={`${styles.collectionCard} animate-fade-in-up delay-${i + 1}`}
                >
                  <img src={col.image} alt={col.name} className={styles.collectionImage} loading="lazy" />
                  <div className={styles.collectionOverlay} />
                  <div className={styles.collectionInfo}>
                    <span className={styles.collectionCount}>{col.productCount} Pieces</span>
                    <h3 className={styles.collectionName}>{col.name}</h3>
                    <p className={styles.collectionDesc}>{col.description}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* ═══ NEW ARRIVALS GRID ═══ */}
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <div>
                <span className="text-caption">Just Dropped</span>
                <h2 className={`heading-display ${styles.sectionTitle}`}>New Arrivals</h2>
              </div>
              <Link href="/shop?sort=new" className="btn btn-ghost">
                Shop New →
              </Link>
            </div>

            <div className={styles.productGrid}>
              {newArrivals.map((product, i) => (
                <ProductCard key={product.id} product={product} index={i} />
              ))}
            </div>
          </div>
        </section>

        {/* ═══ NEWSLETTER ═══ */}
        <section className={styles.newsletter}>
          <div className={`container ${styles.newsletterInner}`}>
            <span className="text-caption">Inner Circle</span>
            <h2 className={`heading-display ${styles.newsletterTitle}`}>
              Get early access to every drop
            </h2>
            <p className={styles.newsletterSub}>
              Subscribers see new pieces 24 hours before everyone else. No spam. Just drops.
            </p>
            {newsletterSubmitted ? (
              <p style={{ color: 'var(--accent-gold)', fontSize: '0.9rem', letterSpacing: '0.1em' }}>✦ Welcome to the inner circle. You're in.</p>
            ) : (
              <form className={styles.newsletterForm} onSubmit={(e) => { e.preventDefault(); if (newsletterEmail) setNewsletterSubmitted(true); }}>
                <input
                  type="email"
                  placeholder="Enter your email"
                  className={styles.newsletterInput}
                  aria-label="Email address"
                  value={newsletterEmail}
                  onChange={(e) => setNewsletterEmail(e.target.value)}
                />
                <button type="submit" className="btn btn-primary">Join</button>
              </form>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
