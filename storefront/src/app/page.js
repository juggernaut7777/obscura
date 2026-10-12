"use client";
import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useCart } from "@/context/CartContext";
import { useCurrency } from "@/context/CurrencyContext";
import { sound } from "@/utils/sound";
import Header from "@/components/Header";
import ProductCard from "@/components/ProductCard";
import CartSidebar from "@/components/CartSidebar";
import Footer from "@/components/Footer";
import { DEMO_PRODUCTS, COLLECTIONS } from "@/data/products";
import styles from "./page.module.css";

export default function Home() {
  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem, addToCart } = useCart();
  const { formatPrice } = useCurrency();
  const [newsletterSubmitted, setNewsletterSubmitted] = useState(false);
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [activeLook, setActiveLook] = useState(0);
  const [hotspotAdded, setHotspotAdded] = useState(false);

  // Find the best editorial lookbook image for each product (skip selfies, flat lays)
  const getBestLookbookImage = (product) => {
    if (!product?.images) return "/images/editorial_hero.jpg";
    const editorial = product.images.find(
      (img) =>
        (img.includes("lookbook") || img.includes("editorial") || img.includes("on_model")) &&
        !img.includes("selfie") &&
        !img.includes("mirror")
    );
    return editorial || product.images.find((img) => !img.includes("flat_lay") && !img.includes("selfie") && !img.includes("mirror")) || product.images[0];
  };

  // Curated Runway Looks — split-screen hero showcase
  const runwayLooks = [
    {
      id: "look-01",
      number: "01",
      drop: "DROP 04",
      title: "WASHED CAMO DIPLOMATIC SET",
      subtitle: "Brutalist Dropped Shoulder",
      spec: "480 GSM French Terry",
      detail: "Cold Wash Patina #09 — Deconstructed Raw Hem",
      product: DEMO_PRODUCTS.find((p) => p.id.includes("camo")) || DEMO_PRODUCTS[0],
    },
    {
      id: "look-02",
      number: "02",
      drop: "DROP 04",
      title: "VINTAGE HEAVYWEIGHT BOXY HOODIE",
      subtitle: "Architectural Boxy Cropped",
      spec: "520 GSM Loopback Fleece",
      detail: "Mineral Vintage Grey Wash — Extended Double-Knit Cuffs",
      product: DEMO_PRODUCTS.find((p) => p.id.includes("hoodie")) || DEMO_PRODUCTS[1],
    },
    {
      id: "look-03",
      number: "03",
      drop: "DROP 04",
      title: "STRUCTURAL SHELL RUNWAY JACKET",
      subtitle: "High-Neck Funnel Geometry",
      spec: "Weather-Sealed Milled Nylon",
      detail: "Stealth Matte Noir — Geometric Technical Paneling",
      product: DEMO_PRODUCTS.find((p) => p.id.includes("jacket")) || DEMO_PRODUCTS[2],
    },
    {
      id: "look-04",
      number: "04",
      drop: "DROP 04",
      title: "HEAVYWEIGHT DRAPED ESSENTIAL TEE",
      subtitle: "Boxy Relaxed Torso",
      spec: "300 GSM Combed Cotton",
      detail: "Reactive Black Zero-Shrink — Structural Combed Rib",
      product: DEMO_PRODUCTS.find((p) => p.id.includes("essential") || p.id.includes("tee")) || DEMO_PRODUCTS[3],
    },
  ];

  const currentLook = runwayLooks[activeLook];

  const handleNextLook = () => {
    sound.playSubBass();
    setActiveLook((prev) => (prev + 1) % runwayLooks.length);
    setHotspotAdded(false);
  };

  const handlePrevLook = () => {
    sound.playSubBass();
    setActiveLook((prev) => (prev - 1 + runwayLooks.length) % runwayLooks.length);
    setHotspotAdded(false);
  };

  const handleHotspotQuickAdd = (product) => {
    if (!product) return;
    sound.playChime();
    addToCart(
      {
        ...product,
        id: `${product.id}-l`,
        productId: product.id,
        size: product.sizes?.[1] || "L",
        image: product.images?.[0],
      },
      1
    );
    setHotspotAdded(true);
    setTimeout(() => setHotspotAdded(false), 2400);
  };

  const featured = DEMO_PRODUCTS.slice(0, 8);
  const newArrivals = DEMO_PRODUCTS.slice(0, 16);

  // Deduplicate video products — only show unique video URLs
  const videoProducts = useMemo(() => {
    const seen = new Set();
    return DEMO_PRODUCTS.filter((p) => {
      if (!p.videoUrl || seen.has(p.videoUrl)) return false;
      seen.add(p.videoUrl);
      return true;
    }).slice(0, 4);
  }, []);

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
        {/* ═══ SPLIT-SCREEN VOGUE HERO ═══ */}
        <section className={styles.heroSection}>
          {/* Fixed cinematic background — main_hero_bg.jpg (1400×788 architectural gallery) */}
          <div className={styles.heroBgWrap}>
            <img
              src="/images/main_hero_bg.jpg"
              alt=""
              className={styles.heroBgImage}
              aria-hidden="true"
            />
            <div className={styles.heroBgOverlay} />
            <div className={styles.heroGrain} />
          </div>

          {/* Split-Screen Content */}
          <div className={`container ${styles.heroSplit}`}>
            {/* LEFT COLUMN — Editorial Typography */}
            <div className={styles.heroLeft}>
              <div className={styles.heroMeta}>
                <span className={styles.heroMetaTag}>LOOK {currentLook.number}</span>
                <span className={styles.heroMetaDivider}>/</span>
                <span className={styles.heroMetaDrop}>{currentLook.drop}</span>
              </div>

              <h1 className={styles.heroTitle}>
                {currentLook.title}
              </h1>

              <p className={styles.heroSubtitle}>{currentLook.subtitle}</p>

              <div className={styles.heroSpecBlock}>
                <div className={styles.heroSpecRow}>
                  <span className={styles.heroSpecLabel}>FABRICATION</span>
                  <span className={styles.heroSpecValue}>{currentLook.spec}</span>
                </div>
                <div className={styles.heroSpecRow}>
                  <span className={styles.heroSpecLabel}>TREATMENT</span>
                  <span className={styles.heroSpecValue}>{currentLook.detail}</span>
                </div>
                {currentLook.product && (
                  <div className={styles.heroSpecRow}>
                    <span className={styles.heroSpecLabel}>ALLOCATION</span>
                    <span className={styles.heroSpecValue}>{formatPrice(currentLook.product.price)}</span>
                  </div>
                )}
              </div>

              <div className={styles.heroCTAs}>
                <Link href="/shop" className="btn btn-primary" onClick={() => sound.playClick()}>
                  ENTER ARCHIVE
                </Link>
                <Link href="/lookbook" className="btn btn-outline" onClick={() => sound.playClick()}>
                  VIEW EDITORIAL
                </Link>
              </div>

              {/* Look Navigation */}
              <div className={styles.heroNav}>
                <button className={styles.heroNavArrow} onClick={handlePrevLook} aria-label="Previous Look">
                  &larr;
                </button>
                <div className={styles.heroNavDots}>
                  {runwayLooks.map((look, idx) => (
                    <button
                      key={look.id}
                      className={`${styles.heroNavDot} ${idx === activeLook ? styles.heroNavDotActive : ""}`}
                      onClick={() => {
                        sound.playSubBass();
                        setActiveLook(idx);
                      }}
                      aria-label={`Look ${idx + 1}`}
                    >
                      {String(idx + 1).padStart(2, "0")}
                    </button>
                  ))}
                </div>
                <button className={styles.heroNavArrow} onClick={handleNextLook} aria-label="Next Look">
                  &rarr;
                </button>
              </div>
            </div>

            {/* RIGHT COLUMN — Lookbook Product Image with Architectural Framing */}
            <div className={styles.heroRight}>
              <div className={styles.heroImageFrame}>
                <img
                  key={currentLook.id}
                  src={getBestLookbookImage(currentLook.product)}
                  alt={currentLook.title}
                  className={styles.heroProductImage}
                />
                {/* Product Quick-Allocate Overlay — bottom of image, never collides with left text */}
                {currentLook.product && (
                  <div className={styles.heroImageOverlay}>
                    <div className={styles.heroImageMeta}>
                      <span className={styles.heroImageSpec}>{currentLook.spec}</span>
                      <span className={styles.heroImagePrice}>{formatPrice(currentLook.product.price)}</span>
                    </div>
                    <div className={styles.heroImageActions}>
                      <button
                        type="button"
                        className={`${styles.heroAllocateBtn} ${hotspotAdded ? styles.heroAllocateSuccess : ""}`}
                        onClick={() => handleHotspotQuickAdd(currentLook.product)}
                      >
                        {hotspotAdded ? "ALLOCATED \u2713" : "QUICK ALLOCATE — SIZE L"}
                      </button>
                      <Link
                        href={`/product/${currentLook.product.id}`}
                        className={styles.heroInspectBtn}
                        onClick={() => sound.playClick()}
                      >
                        INSPECT
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* ═══ INDUSTRIAL TICKER ═══ */}
        <div className={styles.marquee}>
          <div className={styles.marqueeTrack}>
            {[...Array(3)].map((_, i) => (
              <span key={i} className={styles.marqueeText}>
                OBSCURA ATELIER &mdash; 520 GSM LOOPBACK FLEECE &mdash; DDP WORLDWIDE AIR LOGISTICS &mdash; ALL IMPORT DUTIES PREPAID &mdash; STRICT LIMITED ALLOCATIONS &mdash; ZERO COMMERCIAL RESTOCKS &nbsp;&bull;&nbsp;
              </span>
            ))}
          </div>
        </div>

        {/* ═══ ATELIER PROTOCOL (CRAFTSMANSHIP SPEC) ═══ */}
        <section className={styles.protocolSection}>
          <div className="container">
            <div className={styles.protocolHeader}>
              <span className="tag-spec">MATERIAL INTELLIGENCE</span>
              <h2 className={`heading-display ${styles.protocolTitle}`}>ATELIER PROTOCOL</h2>
            </div>
            <div className={styles.protocolGrid}>
              <div className={styles.protocolCard}>
                <span className={styles.protocolNumber}>01</span>
                <h4 className={styles.protocolHeading}>520 GSM HEAVYWEIGHT MILLING</h4>
                <p className={styles.protocolDesc}>
                  Custom-milled 480–520 GSM loopback cotton fleece and 300 GSM combed jersey. Structural geometry that maintains silhouette through prolonged wear.
                </p>
              </div>
              <div className={styles.protocolCard}>
                <span className={styles.protocolNumber}>02</span>
                <h4 className={styles.protocolHeading}>DECONSTRUCTED CUTS</h4>
                <p className={styles.protocolDesc}>
                  Drop-shoulder drape, cropped boxy hemlines, and extended double-rib cuffs. Modeled on brutalist proportions with zero commercial shortcuts.
                </p>
              </div>
              <div className={styles.protocolCard}>
                <span className={styles.protocolNumber}>03</span>
                <h4 className={styles.protocolHeading}>DDP AIR LOGISTICS</h4>
                <p className={styles.protocolDesc}>
                  Dispatched via expedited DDP air couriers from Guangzhou ateliers. Customs clearance, import duties, and local delivery fully prepaid.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ═══ FEATURED PRODUCTS ═══ */}
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <div>
                <span className="tag-spec">ARCHIVE SELECTION</span>
                <h2 className={`heading-display ${styles.sectionTitle}`}>CORE SILHOUETTES</h2>
              </div>
              <Link href="/shop" className="btn btn-ghost" onClick={() => sound.playClick()}>
                ALL PIECES &rarr;
              </Link>
            </div>

            <div className={styles.productGrid}>
              {featured.map((product, i) => (
                <ProductCard key={product.id} product={product} index={i} />
              ))}
            </div>
          </div>
        </section>

        {/* ═══ MOTION ARCHIVE (9:16 VIDEO) — Deduplicated ═══ */}
        {videoProducts.length > 0 && (
          <section className={styles.section} style={{ borderTop: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)", background: "#050505" }}>
            <div className="container">
              <div className={styles.sectionHeader}>
                <div>
                  <span className="tag-spec-gold">IN-SITU MOTION ARCHIVE</span>
                  <h2 className={`heading-display ${styles.sectionTitle}`}>FABRIC IN MOTION</h2>
                </div>
                <Link href="/shop" className="btn btn-ghost" onClick={() => sound.playClick()}>
                  EXPLORE DROPS &rarr;
                </Link>
              </div>

              <div className={styles.videoGrid}>
                {videoProducts.map((p) => (
                  <div key={p.id} className={styles.videoCard}>
                    <video
                      src={p.videoUrl}
                      autoPlay
                      muted
                      loop
                      playsInline
                      className={styles.videoPlayer}
                    />
                    <div className={styles.videoOverlay}>
                      <div className={styles.videoMeta}>
                        <span className={styles.videoTag}>IN-SITU MOTION</span>
                        <span className={styles.videoDuration}>10.0S</span>
                      </div>
                      <Link href={`/product/${p.id}`} className={styles.videoTitle}>
                        {p.name}
                      </Link>
                      <span className={styles.videoPrice}>{formatPrice(p.price)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* ═══ EDITORIAL PHILOSOPHY (VOGUE SPREAD) ═══ */}
        <section className={styles.editorial}>
          <div className={`container ${styles.editorialInner}`}>
            <div className={styles.editorialText}>
              <span className="tag-spec">ATELIER PHILOSOPHY</span>
              <h2 className={`heading-display ${styles.editorialTitle}`}>
                ENGINEERED PERMANENCE.
                <br />
                <span className="heading-vogue">Zero Disposable Trends.</span>
              </h2>
              <p className={styles.editorialBody}>
                We collaborate directly with independent pattern makers and specialized fabric mills across Guangzhou and Hangzhou. Every garment is fabricated with structural intent — heavyweight combed cottons, cold-dye wash baths, and milled titanium-finish hardware. Restocks are strictly never guaranteed.
              </p>
              <div>
                <Link href="/lookbook" className="btn btn-outline" onClick={() => sound.playClick()}>
                  READ EDITORIAL MANIFESTO
                </Link>
              </div>
            </div>
            <div className={styles.editorialImage}>
              {/* Locked to editorial_hero.jpg — never falls back to product card images */}
              <img
                src="/images/editorial_hero.jpg"
                alt="OBSCURA Haute Couture Editorial"
                loading="lazy"
              />
            </div>
          </div>
        </section>

        {/* ═══ ARCHIVAL COLLECTIONS ═══ */}
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <div>
                <span className="tag-spec">CURATED ARCHIVES</span>
                <h2 className={`heading-display ${styles.sectionTitle}`}>SERIES ARCHIVE</h2>
              </div>
            </div>

            <div className={styles.collectionsGrid}>
              {COLLECTIONS.map((col, i) => (
                <Link
                  key={col.id}
                  href="/shop"
                  className={`${styles.collectionCard} animate-fade-in-up delay-${i + 1}`}
                  onClick={() => sound.playClick()}
                >
                  <img src={col.image} alt={col.name} className={styles.collectionImage} loading="lazy" />
                  <div className={styles.collectionOverlay} />
                  <div className={styles.collectionInfo}>
                    <span className={styles.collectionCount}>{col.productCount} PIECES</span>
                    <h3 className={styles.collectionName}>{col.name}</h3>
                    <p className={styles.collectionDesc}>{col.description}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* ═══ NEW ARRIVALS ═══ */}
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeader}>
              <div>
                <span className="tag-spec">RECENT ACQUISITIONS</span>
                <h2 className={`heading-display ${styles.sectionTitle}`}>LATEST DISPATCHES</h2>
              </div>
              <Link href="/shop?sort=new" className="btn btn-ghost" onClick={() => sound.playClick()}>
                ALL RELEASES &rarr;
              </Link>
            </div>

            <div className={styles.productGrid}>
              {newArrivals.map((product, i) => (
                <ProductCard key={product.id} product={product} index={i} />
              ))}
            </div>

            <div style={{ textAlign: "center", marginTop: "3rem" }}>
              <Link 
                href="/shop" 
                className="btn btn-primary" 
                style={{ padding: "14px 36px", letterSpacing: "0.15em", textTransform: "uppercase", fontSize: "0.85rem" }} 
                onClick={() => sound.playClick()}
              >
                VIEW COMPLETE ARCHIVE ({DEMO_PRODUCTS.length} PIECES) &rarr;
              </Link>
            </div>
          </div>
        </section>

        {/* ═══ NEWSLETTER ═══ */}
        <section className={styles.newsletter}>
          <div className={`container ${styles.newsletterInner}`}>
            <span className="tag-spec-gold">PRIORITY ACCESS</span>
            <h2 className={`heading-display ${styles.newsletterTitle}`}>
              ARCHIVE DISPATCH
            </h2>
            <p className={styles.newsletterSub}>
              Registered collectors receive lookbook previews and allocation access 24 hours prior to public release.
            </p>
            {newsletterSubmitted ? (
              <p className={styles.newsletterConfirm}>
                CONFIRMED — DISPATCH REGISTERED
              </p>
            ) : (
              <form
                className={styles.newsletterForm}
                onSubmit={(e) => {
                  e.preventDefault();
                  if (newsletterEmail) {
                    sound.playChime();
                    setNewsletterSubmitted(true);
                  }
                }}
              >
                <input
                  type="email"
                  placeholder="EMAIL ADDRESS"
                  className={styles.newsletterInput}
                  aria-label="Email address"
                  value={newsletterEmail}
                  onChange={(e) => setNewsletterEmail(e.target.value)}
                />
                <button type="submit" className="btn btn-primary">
                  REGISTER
                </button>
              </form>
            )}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
