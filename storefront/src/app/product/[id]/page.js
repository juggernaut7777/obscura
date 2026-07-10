"use client";
import { use, useState } from "react";
import Link from "next/link";
import { useCart } from "@/context/CartContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import ProductCard from "@/components/ProductCard";
import { DEMO_PRODUCTS } from "@/data/products";
import styles from "./page.module.css";

export default function ProductPage({ params }) {
  // Unwrap params using React.use()
  const unwrappedParams = use(params);
  
  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem, addToCart: contextAddToCart } = useCart();
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
  
  // Find product
  const product = DEMO_PRODUCTS.find((p) => p.id === unwrappedParams.id) || DEMO_PRODUCTS[0];
  
  // Color variant support (handles both string and object color representations)
  const hasColors = product.colors && product.colors.length > 0;
  const activeColor = hasColors ? product.colors[selectedColor] : null;
  const activeColorName = activeColor ? (typeof activeColor === "object" ? activeColor.name : activeColor) : null;
  
  const fallbackImages = ["/placeholder.jpg"];
  const activeColorImages = activeColor && typeof activeColor === "object" && activeColor.images && activeColor.images.length > 0
    ? activeColor.images
    : (product.images && product.images.length > 0 ? product.images : fallbackImages);
  
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
            <div className={styles.thumbnails}>
              {activeColorImages.map((img, idx) => (
                <button
                  key={idx}
                  className={`${styles.thumbBtn} ${activeImage === idx ? styles.activeThumb : ""}`}
                  onClick={() => setActiveImage(idx)}
                >
                  <img src={img} alt={`Thumbnail ${idx + 1}`} />
                </button>
              ))}
            </div>
            <div className={`${styles.mainImageWrap} ${tryonActive ? styles.scanning : ""}`}>
              <img
                src={tryonImage || activeColorImages[activeImage] || activeColorImages[0]}
                alt={product.name}
                className={`${styles.mainImage} animate-fade-in`}
                key={`${selectedColor}-${activeImage}-${tryonImage}`}
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
          </div>

          {/* Info */}
          <div className={`${styles.info} animate-fade-in-up delay-2`}>
            <div className={styles.infoHeader}>
              <span className="text-caption">{product.category}</span>
              <h1 className={`heading-display ${styles.title}`}>{product.name}</h1>
              <div className={styles.priceRow}>
                <span className={styles.price}>${product.price.toFixed(2)}</span>
                {product.comparePrice > 0 && (
                  <span className={styles.comparePrice}>${product.comparePrice.toFixed(2)}</span>
                )}
              </div>
            </div>

            {/* Color Swatches */}
            {hasColors && (
              <div className={styles.selector}>
                <div className={styles.selectorHeader}>
                  <span className={styles.selectorLabel}>Color — {activeColorName}</span>
                </div>
                <div className={styles.colorSwatches}>
                  {product.colors.map((color, idx) => {
                    const name = typeof color === "object" ? color.name : color;
                    const hex = typeof color === "object" ? color.hex : COLOR_HEX_MAP[name.toLowerCase()] || "#888888";
                    return (
                      <button
                        key={idx}
                        className={`${styles.colorSwatch} ${selectedColor === idx ? styles.selectedSwatch : ""}`}
                        onClick={() => { setSelectedColor(idx); setActiveImage(0); }}
                        title={name}
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
                  opacity: selectedSize && !product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false ? 1 : (selectedSize ? 0.5 : 1), 
                  cursor: selectedSize && !product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false ? "pointer" : (selectedSize ? "not-allowed" : "pointer")
                }}
                onClick={addToCart}
                disabled={selectedSize && product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false}
              >
                {selectedSize && product.stock_status?.[`${activeColorName || "Default"}-${selectedSize}`] === false ? "Out of Stock" : "Add to Bag"}
              </button>
              
              <button 
                className="btn" 
                style={{ 
                  width: "100%", 
                  padding: "1rem", 
                  background: "linear-gradient(135deg, #D4AF37 0%, #B8860B 100%)",
                  color: "#000",
                  fontWeight: "bold",
                  border: "none",
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
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
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
                {tryonImage ? "Reset Product View" : "Virtual Try-On"}
              </button>
              
              <p className={styles.shippingInfo}>
                Free shipping on orders over $99. Free returns within 30 days.
              </p>
            </div>

            {/* Details Accordion (Simulated) */}
            <div className={styles.detailsList}>
              <h3 className={styles.detailsTitle}>The Details</h3>
              <ul className={styles.bulletList}>
                {product.details.map((detail, i) => (
                  <li key={i}>{detail}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

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
            <h2 className={styles.modalTitle}>CHOOSE VIRTUAL MODEL</h2>
            
            <div className={styles.modelsGrid}>
              {/* Model 1: f1 */}
              <div 
                className={`${styles.modelCard} ${selectedModel === "f1" ? styles.modelCardActive : ""}`}
                onClick={() => setSelectedModel("f1")}
              >
                <div className={styles.modelAvatar} style={{ background: "#D4AF37", color: "#000" }}>F1</div>
                <span className={styles.modelName}>Female 1</span>
                <span className={styles.modelMeta}>Athletic | S</span>
              </div>

              {/* Model 2: f2 */}
              <div 
                className={`${styles.modelCard} ${selectedModel === "f2" ? styles.modelCardActive : ""}`}
                onClick={() => setSelectedModel("f2")}
              >
                <div className={styles.modelAvatar} style={{ background: "#C0C0C0", color: "#000" }}>F2</div>
                <span className={styles.modelName}>Female 2</span>
                <span className={styles.modelMeta}>Curvy | M</span>
              </div>

              {/* Model 3: m1 */}
              <div 
                className={`${styles.modelCard} ${selectedModel === "m1" ? styles.modelCardActive : ""}`}
                onClick={() => setSelectedModel("m1")}
              >
                <div className={styles.modelAvatar} style={{ background: "#CD7F32", color: "#000" }}>M1</div>
                <span className={styles.modelName}>Male 1</span>
                <span className={styles.modelMeta}>Muscular | L</span>
              </div>
            </div>

            <button 
              className="btn btn-primary" 
              style={{ width: "100%", background: "linear-gradient(135deg, #D4AF37 0%, #B8860B 100%)", color: "#000", border: "none", fontWeight: "bold" }}
              onClick={() => {
                setTryonOpen(false);
                setTryonActive(true);
                setTryonPhase("Mapping Garment...");
                
                setTimeout(() => {
                  setTryonPhase(`Dressing ${selectedModel.toUpperCase()} Model...`);
                  
                  setTimeout(() => {
                    setTryonPhase("Enhancing Quality...");
                    
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
                }, 1200);
              }}
            >
              Generate Try-On
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
              {product.size_chart_image ? (
                <div style={{ background: "#1a1a1a", padding: "10px", borderRadius: "8px", border: "1px solid #333", overflow: "hidden" }}>
                  <img 
                    src={product.size_chart_image} 
                    alt={`${product.name} Size Chart`} 
                    style={{ width: "100%", height: "auto", objectFit: "contain", maxHeight: "400px" }} 
                  />
                </div>
              ) : (
                <div style={{ padding: "40px 20px", textAlign: "center", border: "1px dashed #333", borderRadius: "8px" }}>
                  <p style={{ color: "#a0a0a0" }}>No size chart image uploaded for this product.</p>
                </div>
              )}
              
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
