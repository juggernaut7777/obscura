"use client";
import { use, useState } from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { useCart } from "@/context/CartContext";
import { useCurrency } from "@/context/CurrencyContext";
import { sound } from "@/utils/sound";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import ProductCard from "@/components/ProductCard";
import { DEMO_PRODUCTS } from "@/data/products";
import styles from "./page.module.css";

const COLOR_HEX_MAP = {
  "black": "#111111", "white": "#ffffff", "grey": "#64748b", "gray": "#64748b",
  "navy": "#0f172a", "blue": "#2563eb", "red": "#dc2626", "green": "#166534",
  "cream": "#fef3c7", "khaki": "#78350f", "camel": "#b45309", "brown": "#451a03",
  "light_blue": "#60a5fa", "light blue": "#60a5fa", "sky_blue": "#38bdf8",
  "army green": "#4b5320", "army_green": "#4b5320",
  "dark blue": "#0f172a", "dark_blue": "#0f172a", "navy blue": "#1e3a8a", "navy_blue": "#1e3a8a",
  "dark gray": "#334155", "dark_gray": "#334155", "dark grey": "#334155", "dark_grey": "#334155",
  "deep red": "#800020", "deep_red": "#800020",
  "wine red": "#701a75", "wine_red": "#701a75",
  "tangerine red": "#ea580c", "tangerine_red": "#ea580c",
  "off-white": "#f8fafc", "off_white": "#f8fafc", "offwhite": "#f8fafc",
  "yellow": "#eab308", "pink": "#ec4899"
};

export default function ProductPage({ params }) {
  // Unwrap params using React.use()
  const unwrappedParams = use(params);
  
  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem, addToCart: contextAddToCart } = useCart();
  const { formatPrice } = useCurrency();
  const [activeImage, setActiveImage] = useState(0);
  const [selectedSize, setSelectedSize] = useState(null);
  const [selectedColor, setSelectedColor] = useState(0);
  
  // VTON Try-On Widget States
  const [tryonOpen, setTryonOpen] = useState(false);
  const [tryonActive, setTryonActive] = useState(false);
  const [tryonPhase, setTryonPhase] = useState("");
  const [selectedModel, setSelectedModel] = useState("f1");
  const [tryonImage, setTryonImage] = useState(null);
  const [sizeGuideOpen, setSizeGuideOpen] = useState(false);
  const [photosOpen, setPhotosOpen] = useState(false);
  const [mediaTab, setMediaTab] = useState("photos"); // "photos" | "video"
  const [videoMuted, setVideoMuted] = useState(true);
  
  // Find product
  const product = DEMO_PRODUCTS.find((p) => p.id === unwrappedParams.id);
  if (!product) notFound();

  const FOOTWEAR_ANGLES = ["Profile View", "On-Foot Flex", "Top-Down", "Heel & Sole", "Unboxing", "Box & Tags"];
  const isShoes = Boolean(
    product.isFootwear ||
    (product.category && product.category.toLowerCase().includes("shoe")) ||
    (product.name && /shoe|sneaker|boot|trainer|dunk|jordan/i.test(product.name))
  );
  
  // Color variant support (handles both string and object color representations)
  const hasColors = product.colors && product.colors.length > 0;
  const activeColor = hasColors ? product.colors[selectedColor] : null;
  const activeColorName = activeColor ? (typeof activeColor === "object" ? activeColor.name : activeColor) : null;
  
  const fallbackImages = ["/images/main_hero_bg.jpg"];
  const activeColorImages = activeColor && typeof activeColor === "object" && activeColor.images && activeColor.images.length > 0
    ? activeColor.images
    : (product.images && product.images.length > 0 ? product.images : fallbackImages);
  const safeActiveImage = Math.min(activeImage, activeColorImages.length - 1);
  
  // Curated Vogue Editorial Shoots
  const editorialStills = [
    ...(product.lookbookImages || []),
    ...(product.images || []).filter(img => 
      /on_model|model|lookbook|outfit|editorial/i.test(img) && !/selfie|chart/i.test(img)
    )
  ].filter((img, idx, arr) => {
    const url = typeof img === 'string' ? img : img.url;
    return arr.findIndex(x => (typeof x === 'string' ? x : x.url) === url) === idx;
  });

  // Find related products
  const related = DEMO_PRODUCTS.filter(
    (p) => p.category === product.category && p.id !== product.id
  ).slice(0, 4);

  const addToCart = () => {
    if (!selectedSize && product.sizes?.length > 0) {
      alert("Please select a size first.");
      return;
    }
    
    const colorTag = activeColorName ? `-${activeColorName.toLowerCase()}` : '';
    const cartItemId = `${product.id}${colorTag}-${selectedSize || 'os'}`;
    
    // Create cart item format
    const cartItem = {
      ...product,
      id: cartItemId, // Overwrite with specific variant ID
      productId: product.id,
      name: activeColorName ? `${product.name} — ${activeColorName}` : product.name,
      image: activeColorImages[0],
      size: selectedSize,
      color: activeColorName
    };
    
    contextAddToCart(cartItem, 1);
  };

  const NON_COLOR_KEYS = ['group_shots', 'group shots', 'size_chart', 'details'];
  const filteredColors = hasColors ? product.colors
    .map((color, originalIdx) => ({ color, originalIdx }))
    .filter(({ color }) => {
      const n = (typeof color === 'object' ? color.name : color).toLowerCase();
      return !NON_COLOR_KEYS.includes(n);
    }) : [];

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
        {/* Breadcrumbs */}
        <div className="container">
          <div className={styles.breadcrumbs}>
            <Link href="/">Home</Link>
            <span>/</span>
            <Link href="/shop">Shop</Link>
            <span>/</span>
            <span className={styles.currentCrumb}>{product.name}</span>
          </div>
        </div>

        {/* Product Section */}
        <section className={`container ${styles.productSection}`}>
          {/* Gallery */}
          <div className={styles.gallery}>
            {/* Media Mode Switcher */}
            {product.videoUrl && (
              <div style={{ display: "flex", gap: "8px", marginBottom: "14px", width: "100%" }}>
                <button
                  type="button"
                  onClick={() => setMediaTab("photos")}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "var(--radius-sm)",
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.68rem",
                    fontWeight: 500,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    border: "1px solid var(--border-subtle)",
                    cursor: "pointer",
                    background: mediaTab === "photos" ? "#ffffff" : "#0d0d0d",
                    color: mediaTab === "photos" ? "#000000" : "var(--text-secondary)",
                    transition: "all 0.2s"
                  }}
                >
                  [ 01 / LOOKBOOK STILLS ]
                </button>
                <button
                  type="button"
                  onClick={() => setMediaTab("video")}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "var(--radius-sm)",
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.68rem",
                    fontWeight: 500,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    border: "1px solid var(--border-subtle)",
                    cursor: "pointer",
                    background: mediaTab === "video" ? "#ffffff" : "#0d0d0d",
                    color: mediaTab === "video" ? "#000000" : "var(--text-secondary)",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    transition: "all 0.2s"
                  }}
                >
                  <span>[ 02 / MOTION ARCHIVE ]</span>
                  <span style={{ fontSize: "0.6rem", background: "rgba(197, 160, 89, 0.2)", color: "var(--accent-gold)", padding: "1px 5px", borderRadius: "2px" }}>10.0S</span>
                </button>
              </div>
            )}

            {mediaTab === "video" && product.videoUrl ? (
              <div style={{
                position: "relative",
                width: "100%",
                maxWidth: "460px",
                aspectRatio: "9/16",
                margin: "0 auto",
                borderRadius: "var(--radius-sm)",
                overflow: "hidden",
                background: "#060606",
                border: "1px solid var(--border-medium)",
                boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.9)"
              }}>
                <video
                  src={product.videoUrl}
                  autoPlay
                  loop
                  playsInline
                  muted={videoMuted}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />

                {/* Header Tag */}
                <div style={{
                  position: "absolute",
                  top: "16px",
                  left: "16px",
                  right: "16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  zIndex: 5
                }}>
                  <div style={{
                    background: "rgba(6,6,6,0.8)",
                    backdropFilter: "blur(12px)",
                    color: "#fff",
                    padding: "6px 12px",
                    borderRadius: "var(--radius-sm)",
                    fontSize: "0.65rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    border: "1px solid var(--border-subtle)"
                  }}>
                    <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--accent-gold)", display: "inline-block" }} />
                    <span style={{ fontFamily: "var(--font-mono)", letterSpacing: "0.12em", textTransform: "uppercase" }}>IN-SITU MOTION SPEC // 9:16</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => setVideoMuted(!videoMuted)}
                    style={{
                      background: "rgba(6,6,6,0.8)",
                      backdropFilter: "blur(12px)",
                      border: "1px solid var(--border-subtle)",
                      color: "#fff",
                      width: "34px",
                      height: "34px",
                      borderRadius: "var(--radius-sm)",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                    title={videoMuted ? "Unmute" : "Mute"}
                    aria-label={videoMuted ? "Unmute audio" : "Mute audio"}
                  >
                    {videoMuted ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                        <line x1="23" y1="9" x2="17" y2="15" />
                        <line x1="17" y1="9" x2="23" y2="15" />
                      </svg>
                    ) : (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                      </svg>
                    )}
                  </button>
                </div>

                {/* Bottom Overlay Info */}
                <div style={{
                  position: "absolute",
                  bottom: 0,
                  left: 0,
                  right: 0,
                  background: "linear-gradient(transparent, rgba(6,6,6,0.95))",
                  padding: "20px 16px 16px",
                  color: "#fff",
                  zIndex: 5
                }}>
                  <div style={{ fontFamily: "var(--font-mono)", fontWeight: 500, fontSize: "0.68rem", color: "var(--accent-gold)", letterSpacing: "0.15em", textTransform: "uppercase" }}>
                    OBSCURA ARCHIVE // ATELIER IN-SITU
                  </div>
                  <div style={{ fontFamily: "var(--font-sans)", fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "4px", textTransform: "uppercase", letterSpacing: "0.02em" }}>
                    {product.name} — Real-world motion &amp; heavyweight structural drape.
                  </div>
                </div>
              </div>
            ) : (
              <>
                <div className={styles.thumbnails}>
                  {activeColorImages.map((img, idx) => (
                    <button
                      key={idx}
                      className={`${styles.thumbBtn} ${safeActiveImage === idx ? styles.activeThumb : ""}`}
                      onClick={() => { setActiveImage(idx); setMediaTab("photos"); }}
                      style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingBottom: isShoes ? "4px" : "0" }}
                    >
                      <img src={img} alt={`Thumbnail ${idx + 1}`} />
                      {isShoes && (
                        <span style={{ fontSize: "0.55rem", color: "#bbb", marginTop: "2px", textAlign: "center", letterSpacing: "0.02em" }}>
                          {FOOTWEAR_ANGLES[idx] || `Angle ${idx + 1}`}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
                <div className={`${styles.mainImageWrap} ${tryonActive ? styles.scanning : ""}`}>
                  <img
                    src={tryonImage || activeColorImages[safeActiveImage] || activeColorImages[0]}
                    alt={product.name}
                    className={`${styles.mainImage} animate-fade-in`}
                    key={`${selectedColor}-${safeActiveImage}-${tryonImage}`}
                    onError={(e) => { e.target.src = '/images/main_hero_bg.jpg'; }}
                  />
                  
                  {tryonActive && (
                    <div className={styles.vtonLoader}>
                      <div className={styles.spinner}></div>
                      <div className={styles.loaderText}>{tryonPhase}</div>
                    </div>
                  )}
                  {tryonImage && (
                    <span className={styles.vtonActiveBadge}>Try-On Active</span>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Info */}
          <div className={`${styles.info} animate-fade-in-up delay-2`}>
            <div className={styles.infoHeader}>
              <span className="text-caption">{product.category}</span>
              {product.brand && product.brand !== 'Unknown' && (
                <p style={{fontSize: '0.7rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#c9a96e', marginBottom: '0.15rem', fontWeight: 600}}>{product.brand}</p>
              )}
              <h1 className={`heading-display ${styles.title}`}>{product.name}</h1>
              <div className={styles.priceRow}>
                <span className={styles.price}>{formatPrice(product.price)}</span>
                {product.comparePrice > 0 && (
                  <span className={styles.comparePrice}>{formatPrice(product.comparePrice)}</span>
                )}
              </div>
            </div>

            {/* Color Swatches */}
            {hasColors && (
              <div className={styles.selector}>
                <div className={styles.selectorHeader}>
                  <span className={styles.selectorLabel}>
                    Color — <strong style={{ color: '#c9a96e', letterSpacing: '0.05em' }}>{activeColorName}</strong>
                  </span>
                </div>
                <div className={styles.colorSwatches}>
                  {filteredColors.map(({ color, originalIdx }) => {
                      const name = typeof color === "object" ? color.name : color;
                      const hex = typeof color === "object" ? color.hex : COLOR_HEX_MAP[name.toLowerCase()] || "#888888";
                      const isSelected = selectedColor === originalIdx;
                      return (
                        <button
                          key={originalIdx}
                          className={`${styles.colorSwatch} ${isSelected ? styles.selectedSwatch : ""}`}
                          onClick={() => { setSelectedColor(originalIdx); setActiveImage(0); }}
                          title={name}
                          aria-label={name}
                        >
                          <span
                            className={styles.swatchInner}
                            style={{ backgroundColor: hex }}
                          />
                        </button>
                      );
                    })}
                </div>
              </div>
            )}

            <p className={styles.description}>{product.description}</p>

            {/* Sizing */}
            {product.sizes && product.sizes.length > 0 && (
              <div className={styles.selector}>
                <div className={styles.selectorHeader}>
                  <span className={styles.selectorLabel}>Size</span>
                  {(product.size_chart_image || product.size_info) && (
                    <button className={styles.guideBtn} onClick={() => setSizeGuideOpen(true)}>Size Guide</button>
                  )}
                </div>
                <div className={styles.sizeGrid}>
                  {product.sizes.map((size) => {
                    const colorKey = activeColorName || "Default";
                    const stockKey = `${colorKey}-${size}`;
                    const isAvailable = product.stock_status ? (product.stock_status[stockKey] ?? true) : true;
                    
                    return (
                      <button
                        key={size}
                        className={`${styles.sizeBtn} ${selectedSize === size ? styles.selectedSize : ""} ${!isAvailable ? styles.sizeDisabled : ""}`}
                        onClick={() => isAvailable && setSelectedSize(size)}
                        disabled={!isAvailable}
                        style={!isAvailable ? { opacity: 0.4, cursor: "not-allowed", textDecoration: "line-through" } : {}}
                      >
                        {size}
                      </button>
                    );
                  })}
                </div>
                {product.size_info && !product.size_info.includes("Could not read") && !product.size_info.includes("Not specified") && (
                  <div className={styles.fitNote}>
                    {product.size_info.includes("Fit:") 
                      ? product.size_info.split("Fit:")[1].trim()
                      : product.size_info}
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className={styles.actions} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <button 
                className="btn btn-primary" 
                style={{ 
                  width: "100%", 
                  padding: "1rem", 
                  opacity: selectedSize && product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false ? 0.4 : 1, 
                  cursor: selectedSize && product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false ? "not-allowed" : "pointer"
                }}
                onClick={addToCart}
                disabled={selectedSize && product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false}
              >
                {selectedSize && product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false ? "[ ARCHIVE ALLOCATION EXHAUSTED ]" : "[ ACQUIRE PIECE // ADD TO BAG ]"}
              </button>
              
              <button 
                className="btn btn-outline" 
                style={{ 
                  width: "100%", 
                  padding: "0.9rem", 
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  letterSpacing: "0.14em",
                  textTransform: "uppercase",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: "10px"
                }}
                onClick={() => {
                  if (tryonImage) {
                    setTryonImage(null);
                  } else {
                    setTryonOpen(true);
                  }
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  {tryonImage ? (
                    <>
                      <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                      <path d="M3 3v5h5"/>
                    </>
                  ) : (
                    <>
                      <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                    </>
                  )}
                </svg>
                {tryonImage ? "[ RESET PRODUCT ARCHIVE VIEW ]" : "[ VIRTUAL ATELIER TRY-ON ]"}
              </button>
              
              <p className={styles.shippingInfo}>
                EXPEDITED DDP AIR TRANSIT // ALL IMPORT TAXES INCLUDED // 30-DAY ARCHIVAL RETURN PROTOCOL
              </p>
            </div>

            {/* Details Accordion */}
            <div className={styles.detailsList}>
              <h3 className={styles.detailsTitle}>GARMENT SPECIFICATIONS</h3>
              <ul className={styles.bulletList}>
                {product.details?.map((detail, i) => (
                  <li key={i}>{detail}</li>
                ))}
              </ul>
              {product.material && (
                <p style={{fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.75rem'}}>
                  <span style={{color: 'var(--accent-gold)', fontWeight: 600}}>FABRICATION:</span> {product.material}
                </p>
              )}
              {product.care && (
                <p style={{fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem'}}>
                  <span style={{color: 'var(--accent-gold)', fontWeight: 600}}>CARE INSTRUCTIONS:</span> {product.care}
                </p>
              )}
              {product.modelInfo && (
                <p style={{fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.25rem'}}>
                  <span style={{color: 'var(--accent-gold)', fontWeight: 600}}>FIT SPECIFICATION:</span> {product.modelInfo}
                </p>
              )}
            </div>

            {/* Product Photos — Real source images */}
            {product.sourceImages && product.sourceImages.length > 0 && (
              <div className={styles.detailsList} style={{marginTop: '1rem'}}>
                <button 
                  onClick={() => setPhotosOpen(!photosOpen)}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer', width: '100%',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.5rem 0', color: '#e0e0e0'
                  }}
                >
                  <h3 className={styles.detailsTitle} style={{margin: 0}}>
                    SOURCE ARCHIVE FLAT LAYS ({product.sourceImages.length})
                  </h3>
                  <span style={{fontSize: '1.1rem', transition: 'transform 0.3s', transform: photosOpen ? 'rotate(180deg)' : 'rotate(0)'}}>
                    ▾
                  </span>
                </button>
                {photosOpen && (
                  <div style={{
                    display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px',
                    marginTop: '0.75rem', animation: 'fadeIn 0.3s ease'
                  }}>
                    {product.sourceImages.map((src, idx) => (
                      <div key={idx} style={{
                        borderRadius: 'var(--radius-sm)', overflow: 'hidden', border: '1px solid var(--border-subtle)',
                        aspectRatio: '1', cursor: 'pointer', transition: 'border-color 0.2s'
                      }}
                        onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-gold)'}
                        onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-subtle)'}
                        onClick={() => window.open(src, '_blank')}
                      >
                        <img src={src} alt={`Detail ${idx + 1}`} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Curated Editorial Runway & Lookbook Gallery */}
        {editorialStills.length > 0 && (
          <section className={styles.editorialSection}>
            <div className="container">
              <div className={styles.editorialHeader}>
                <div className={styles.editorialBadge}>
                  <span className={styles.goldDot}></span>
                  <span>ATELIER ARCHIVE // EDITORIAL STILLS</span>
                </div>
                <h2 className={`heading-display ${styles.editorialTitle}`}>VOGUE EDITORIAL STILLS</h2>
                <p className={styles.editorialSubtitle}>
                  Atmospheric editorial lookbook stills engineered by OBSCURA Atelier — highlighting architectural silhouette drape, heavyweight texture, and high-fashion editorial styling.
                </p>
              </div>

              <div className={styles.editorialGrid}>
                {editorialStills.map((item, idx) => {
                  const src = typeof item === 'string' ? item : item.url;
                  const title = typeof item === 'object' && item.title ? item.title : `EDITORIAL STILL 0${idx + 1}`;
                  const location = typeof item === 'object' && item.location ? item.location : (
                    src.includes('art_gallery') ? 'ARCHITECTURAL ART GALLERY // MINIMALIST MONOLITH' :
                    src.includes('private_jet') ? 'PRIVATE AVIATION HANGAR // RUNWAY CANDID' :
                    src.includes('apres_ski') ? 'ALPINE CHALET // HEAVYWEIGHT DRAPE' :
                    src.includes('recording_studio') ? 'ACOUSTIC ATELIER // NOIR MONOCHROME' :
                    src.includes('brutalist') ? 'LIMESTONE QUARRY // STRUCTURAL TAILORING' :
                    src.includes('art_district') ? 'MODERNIST FACADE // BOX-CUT SILHOUETTE' :
                    src.includes('museum') ? 'GRAND ATRIUM // EDITORIAL ARCHIVE' :
                    'ATELIER RUNWAY STILL'
                  );
                  return (
                    <div key={idx} className={styles.editorialCard}>
                      <div className={styles.editorialImageWrap}>
                        <img 
                          src={src} 
                          alt={`${product.name} Editorial Still ${idx + 1}`} 
                          className={styles.editorialImage} 
                        />
                        <div className={styles.editorialOverlay}>
                          <span className={styles.editorialTag}>{title}</span>
                          <span className={styles.editorialLocation}>{location}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {/* Related Products */}
        {related.length > 0 && (
          <section className={styles.relatedSection}>
            <div className="container">
              <h2 className={`heading-display ${styles.relatedTitle}`}>You may also like</h2>
              <div className={styles.relatedGrid}>
                {related.map((p, i) => (
                  <ProductCard key={p.id} product={p} index={i} />
                ))}
              </div>
            </div>
          </section>
        )}
      </main>

      {/* VTON Model Selection Modal */}
      {tryonOpen && (
        <div className={styles.modalOverlay} onClick={() => setTryonOpen(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <button className={styles.closeBtn} onClick={() => setTryonOpen(false)}>&times;</button>
            <h2 className={styles.modalTitle} style={{ fontFamily: "var(--font-mono)", fontSize: "0.95rem", letterSpacing: "0.18em", textTransform: "uppercase" }}>
              ATELIER FITTING SPECIFICATION // SELECT SILHOUETTE
            </h2>
            
            <div className={styles.modelsGrid}>
              {/* Profile M1 */}
              <div 
                className={`${styles.modelCard} ${selectedModel === "m1" ? styles.modelCardActive : ""}`}
                onClick={() => setSelectedModel("m1")}
                style={{ borderRadius: "2px", border: selectedModel === "m1" ? "1px solid var(--accent-gold)" : "1px solid rgba(255,255,255,0.12)" }}
              >
                <div className={styles.modelAvatar} style={{ background: "rgba(255,255,255,0.06)", color: "var(--accent-gold)", border: "1px solid var(--accent-gold)", borderRadius: "2px" }}>M-01</div>
                <span className={styles.modelName} style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", letterSpacing: "0.1em" }}>PROFILE M-01</span>
                <span className={styles.modelMeta}>MASCULINE // 185CM // SIZE L</span>
              </div>

              {/* Profile F1 */}
              <div 
                className={`${styles.modelCard} ${selectedModel === "f1" ? styles.modelCardActive : ""}`}
                onClick={() => setSelectedModel("f1")}
                style={{ borderRadius: "2px", border: selectedModel === "f1" ? "1px solid var(--accent-gold)" : "1px solid rgba(255,255,255,0.12)" }}
              >
                <div className={styles.modelAvatar} style={{ background: "rgba(255,255,255,0.06)", color: "var(--accent-gold)", border: "1px solid var(--accent-gold)", borderRadius: "2px" }}>F-01</div>
                <span className={styles.modelName} style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", letterSpacing: "0.1em" }}>PROFILE F-01</span>
                <span className={styles.modelMeta}>FEMININE // 175CM // SIZE S</span>
              </div>

              {/* Profile F2 */}
              <div 
                className={`${styles.modelCard} ${selectedModel === "f2" ? styles.modelCardActive : ""}`}
                onClick={() => setSelectedModel("f2")}
                style={{ borderRadius: "2px", border: selectedModel === "f2" ? "1px solid var(--accent-gold)" : "1px solid rgba(255,255,255,0.12)" }}
              >
                <div className={styles.modelAvatar} style={{ background: "rgba(255,255,255,0.06)", color: "var(--accent-gold)", border: "1px solid var(--accent-gold)", borderRadius: "2px" }}>F-02</div>
                <span className={styles.modelName} style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", letterSpacing: "0.1em" }}>PROFILE F-02</span>
                <span className={styles.modelMeta}>OVERSIZED // 172CM // SIZE M</span>
              </div>
            </div>

            <button 
              className="btn btn-primary" 
              style={{ width: "100%", padding: "0.9rem", fontFamily: "var(--font-mono)", fontSize: "0.8rem", letterSpacing: "0.15em", textTransform: "uppercase" }}
              onClick={() => {
                setTryonOpen(false);
                setTryonActive(true);
                setTryonPhase("MAPPING ARCHITECTURAL DRAPE...");
                
                setTimeout(() => {
                  setTryonPhase(`RENDERING ATELIER ${selectedModel.toUpperCase()} SPECIFICATION...`);
                  
                  setTimeout(() => {
                    setTryonPhase("OPTIMIZING TEXTILE RENDER...");
                    
                    setTimeout(() => {
                      setTryonActive(false);
                      // Set try-on result image
                      let targetImg = activeColorImages[0];
                      if (selectedModel === "f2" && activeColorImages.length > 1) {
                        targetImg = activeColorImages[1];
                      } else if (selectedModel === "m1" && activeColorImages.length > 2) {
                        targetImg = activeColorImages[2];
                      } else if (activeColorImages.length > 0) {
                        targetImg = activeColorImages[0];
                      }
                      setTryonImage(targetImg);
                    }, 1200);
                  }, 1200);
                }, 1000);
              }}
            >
              [ INITIATE ATELIER FITTING ]
            </button>
          </div>
        </div>
      )}

      {/* Size Guide Modal */}
      {sizeGuideOpen && (
        <div className={styles.modalOverlay} onClick={() => setSizeGuideOpen(false)}>
          <div className={styles.modal} style={{ maxWidth: "600px" }} onClick={(e) => e.stopPropagation()}>
            <button className={styles.closeBtn} onClick={() => setSizeGuideOpen(false)}>&times;</button>
            <h2 className={styles.modalTitle}>Size Guide</h2>
            
            <div className={styles.sizeGuideContent} style={{ display: "flex", flexDirection: "column", gap: "20px", marginTop: "20px" }}>
              {/* Structured Size Table */}
              {product.sizeGuide && Object.keys(product.sizeGuide).length > 0 && (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", color: "#d5d5d5" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid #c9a96e" }}>
                        <th style={{ padding: "10px 12px", textAlign: "left", color: "#c9a96e", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>Size</th>
                        {Object.keys(Object.values(product.sizeGuide)[0] || {}).map((col) => (
                          <th key={col} style={{ padding: "10px 12px", textAlign: "center", color: "#c9a96e", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>
                            {col.replace('_', ' ')}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(product.sizeGuide).map(([size, measurements], i) => (
                        <tr key={size} style={{ borderBottom: "1px solid #222", background: i % 2 === 0 ? "#111" : "transparent" }}>
                          <td style={{ padding: "10px 12px", fontWeight: "600", color: "#fff" }}>{size}</td>
                          {typeof measurements === "object" && measurements !== null ? (
                            Object.values(measurements).map((val, colIdx) => (
                              <td key={colIdx} style={{ padding: "10px 12px", textAlign: "center" }}>
                                {typeof val === "object" && val !== null ? `${val.cm || val.bust_cm || ""}cm / ${val.in || val.bust_in || ""}″` : String(val)}
                              </td>
                            ))
                          ) : (
                            <td colSpan={4} style={{ padding: "10px 12px", textAlign: "center" }}>{String(measurements)}</td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p style={{ fontSize: "0.7rem", color: "#666", marginTop: "8px", fontStyle: "italic" }}>Bust = half-chest width. 1-3cm variance is normal for hand-measured garments.</p>
                </div>
              )}

              {product.size_chart_image ? (
                <div style={{ background: "#1a1a1a", padding: "10px", borderRadius: "8px", border: "1px solid #333", overflow: "hidden" }}>
                  <img 
                    src={product.size_chart_image} 
                    alt={`${product.name} Size Chart`} 
                    style={{ width: "100%", height: "auto", objectFit: "contain", maxHeight: "400px" }} 
                  />
                </div>
              ) : null}
              
              {product.size_info && (
                <div style={{ background: "#161616", padding: "15px", borderRadius: "8px", border: "1px solid #222" }}>
                  <h4 style={{ color: "#c9a96e", marginBottom: "8px", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Sizing & Fit Advice</h4>
                  <p style={{ fontSize: "0.9rem", color: "#d5d5d5", lineHeight: "1.6" }}>{product.size_info}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <Footer />
    </>
  );
}
