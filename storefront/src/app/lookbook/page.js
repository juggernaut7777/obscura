"use client";
import { useState } from "react";
import Link from "next/link";
import { useCart } from "@/context/CartContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import { DEMO_OUTFITS, DEMO_PRODUCTS } from "@/data/products";
import styles from "./page.module.css";

export default function LookbookPage() {
  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem, addToCart } = useCart();
  
  // Selected outfit for the Interactive Outfit Builder
  const [selectedOutfit, setSelectedOutfit] = useState(null);
  const [builderOpen, setBuilderOpen] = useState(false);
  
  // Outfit builder states: maps productId -> { checked, size, colorIndex }
  const [builderSelections, setBuilderSelections] = useState({});
  const [activeSlide, setActiveSlide] = useState(0);

  const openOutfitBuilder = (outfit) => {
    // Populate linked products from catalog
    const linkedProducts = outfit.products.map(id => DEMO_PRODUCTS.find(p => p.id === id)).filter(Boolean);
    
    // Initialize default selections
    const initialSelections = {};
    linkedProducts.forEach(product => {
      initialSelections[product.id] = {
        checked: true,
        size: product.sizes?.[0] || "OS",
        colorIndex: 0
      };
    });
    
    setSelectedOutfit({
      ...outfit,
      linkedProducts
    });
    setBuilderSelections(initialSelections);
    setActiveSlide(0);
    setBuilderOpen(true);
  };

  const toggleProductChecked = (productId) => {
    setBuilderSelections(prev => ({
      ...prev,
      [productId]: {
        ...prev[productId],
        checked: !prev[productId].checked
      }
    }));
  };

  const handleSizeChange = (productId, size) => {
    setBuilderSelections(prev => ({
      ...prev,
      [productId]: {
        ...prev[productId],
        size
      }
    }));
  };

  const handleColorChange = (productId, colorIndex) => {
    setBuilderSelections(prev => ({
      ...prev,
      [productId]: {
        ...prev[productId],
        colorIndex
      }
    }));
  };

  // Calculate current subtotal based on selections
  const calculateBundleTotal = () => {
    if (!selectedOutfit) return 0;
    return selectedOutfit.linkedProducts.reduce((sum, product) => {
      const select = builderSelections[product.id];
      if (select && select.checked) {
        return sum + product.price;
      }
      return sum;
    }, 0);
  };

  const handleAddBundleToCart = () => {
    if (!selectedOutfit) return;
    
    const itemsToAdd = selectedOutfit.linkedProducts.filter(p => builderSelections[p.id]?.checked);
    
    if (itemsToAdd.length === 0) {
      alert("Please select at least one item to add to the bag.");
      return;
    }
    
    itemsToAdd.forEach(product => {
      const selection = builderSelections[product.id];
      const hasColors = product.colors && product.colors.length > 0;
      const activeColorName = hasColors ? product.colors[selection.colorIndex].name || product.colors[selection.colorIndex] : null;
      const colorImages = hasColors ? product.colors[selection.colorIndex].images || product.images : product.images;
      const colorTag = activeColorName ? `-${activeColorName.toLowerCase()}` : '';
      const cartItemId = `${product.id}${colorTag}-${selection.size}`;
      
      const cartItem = {
        ...product,
        id: cartItemId,
        productId: product.id,
        name: activeColorName ? `${product.name} — ${activeColorName}` : product.name,
        image: colorImages[0] || product.images[0] || "/placeholder.jpg",
        size: selection.size,
        color: activeColorName
      };
      
      addToCart(cartItem, 1);
    });
    
    setBuilderOpen(false);
    setCartOpen(true);
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
        {/* Page Hero */}
        <section className={styles.hero}>
          <div className={styles.heroOverlay} />
          <div className="container">
            <span className="text-caption animate-fade-in-up">AI Campaign Lookbooks</span>
            <h1 className={`heading-display ${styles.title} animate-fade-in-up delay-2`}>
              Style <em>Merges</em>
            </h1>
            <p className={`${styles.subtitle} animate-fade-in-up delay-3`}>
              Explore complete outfits engineered together. Buy the entire visual bundle with 
              shipping consolidation, or customize individual pieces to curate your own look.
            </p>
          </div>
        </section>

        {/* Outfit Campaign Cards Grid */}
        <section className={`container ${styles.gridSection}`}>
          <div className={styles.grid}>
            {DEMO_OUTFITS.map((outfit, index) => (
              <div key={outfit.id} className={styles.outfitCard} onClick={() => openOutfitBuilder(outfit)}>
                <div className={styles.cardImgWrap}>
                  <img src={outfit.image} alt={outfit.name} className={styles.cardImg} loading="lazy" />
                  <div className={styles.cardOverlay} />
                  <div className={styles.badge}>Lookbook Bundle</div>
                  <button className={`btn btn-primary ${styles.cardCTA}`}>Shop Look</button>
                </div>
                <div className={styles.cardInfo}>
                  <div className={styles.tagsRow}>
                    {outfit.tags?.map(t => <span key={t} className={styles.tag}>{t}</span>)}
                  </div>
                  <h3 className={`heading-display ${styles.cardName}`}>{outfit.name}</h3>
                  <p className={styles.cardDesc}>{outfit.description}</p>
                  <div className={styles.cardPriceRow}>
                    <span>Complete Outfit Price</span>
                    <span className={styles.cardPrice}>${outfit.price}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Interactive Outfit Builder Drawer / Modal */}
      {builderOpen && selectedOutfit && (
        <div className={styles.drawerOverlay} onClick={() => setBuilderOpen(false)}>
          <div className={styles.drawer} onClick={(e) => e.stopPropagation()}>
            <button className={styles.closeBtn} onClick={() => setBuilderOpen(false)}>&times;</button>
            
            <div className={styles.drawerInner}>
              {/* Left Column: Sliding Editorial Gallery */}
              <div className={styles.drawerGallery}>
                <div className={styles.sliderWrap}>
                  <img 
                    src={selectedOutfit.images?.[activeSlide] || selectedOutfit.image} 
                    alt={`Lookbook Shot ${activeSlide + 1}`} 
                    className={styles.sliderImg}
                    key={activeSlide}
                  />
                </div>
                {selectedOutfit.images && selectedOutfit.images.length > 1 && (
                  <div className={styles.sliderDots}>
                    {selectedOutfit.images.map((_, idx) => (
                      <button 
                        key={idx} 
                        className={`${styles.dot} ${activeSlide === idx ? styles.activeDot : ""}`}
                        onClick={() => setActiveSlide(idx)}
                        aria-label={`Slide ${idx + 1}`}
                      />
                    ))}
                  </div>
                )}
                <div className={styles.lookbookConcept}>
                  <h4 className={styles.conceptTitle}>Aesthetic Blueprint</h4>
                  <p>{selectedOutfit.description}</p>
                </div>
              </div>

              {/* Right Column: Outfit Builder Panel */}
              <div className={styles.drawerPanel}>
                <span className="text-caption">Outfit Assembler</span>
                <h2 className={`heading-display ${styles.panelTitle}`}>{selectedOutfit.name}</h2>
                
                <div className={styles.productsList}>
                  {selectedOutfit.linkedProducts.map((product) => {
                    const select = builderSelections[product.id] || { checked: true, size: "S", colorIndex: 0 };
                    const hasColors = product.colors && product.colors.length > 0;
                    
                    return (
                      <div key={product.id} className={`${styles.productItem} ${!select.checked ? styles.itemDisabled : ""}`}>
                        {/* Toggle Checkbox */}
                        <div className={styles.toggleWrap}>
                          <input 
                            type="checkbox" 
                            id={`check-${product.id}`}
                            checked={select.checked}
                            onChange={() => toggleProductChecked(product.id)}
                            className={styles.checkbox}
                          />
                          <label htmlFor={`check-${product.id}`} className={styles.checkboxLabel}>
                            <span className={styles.checkboxCustom} />
                          </label>
                        </div>

                        {/* Product Thumbnail */}
                        <img 
                          src={(hasColors ? product.colors[select.colorIndex].images?.[0] : null) || product.images?.[0] || "/placeholder.jpg"} 
                          alt={product.name} 
                          className={styles.productThumb} 
                        />

                        {/* Product Selection Options */}
                        <div className={styles.productDetails}>
                          <div className={styles.productNameRow}>
                            <span className={styles.productName}>{product.name}</span>
                            <span className={styles.productPrice}>${product.price}</span>
                          </div>

                          {select.checked && (
                            <div className={styles.optionsRow}>
                              {/* Color Swatch Selection */}
                              {hasColors && (
                                <div className={styles.optionGroup}>
                                  <span className={styles.optionLabel}>Color:</span>
                                  <div className={styles.swatchList}>
                                    {product.colors.map((c, cIdx) => (
                                      <button
                                        key={cIdx}
                                        className={`${styles.swatch} ${select.colorIndex === cIdx ? styles.activeSwatch : ""}`}
                                        onClick={() => handleColorChange(product.id, cIdx)}
                                        style={{ backgroundColor: (c.hex || c.name || c).toLowerCase().replace(/ /g, '') }}
                                        title={c.name || c}
                                      />
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Size Buttons Selection */}
                              {product.sizes && product.sizes.length > 0 && (
                                <div className={styles.optionGroup}>
                                  <span className={styles.optionLabel}>Size:</span>
                                  <div className={styles.sizesList}>
                                    {product.sizes.map((sz) => (
                                      <button
                                        key={sz}
                                        className={`${styles.sizeTag} ${select.size === sz ? styles.activeSizeTag : ""}`}
                                        onClick={() => handleSizeChange(product.id, sz)}
                                      >
                                        {sz}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Subtotal & Batch Checkout */}
                <div className={styles.panelFooter}>
                  <div className={styles.totalBlock}>
                    <div className={styles.totalLabel}>
                      <span>Consolidated Bundle Total</span>
                      <span className={styles.discountLabel}>Shipping Consolidated</span>
                    </div>
                    <div className={styles.totalPrice}>${calculateBundleTotal()}</div>
                  </div>
                  
                  <button className="btn btn-primary" style={{ width: "100%", padding: "1.2rem" }} onClick={handleAddBundleToCart}>
                    Add Outfit to Bag
                  </button>
                </div>

              </div>
            </div>
            
          </div>
        </div>
      )}

      <Footer />
    </>
  );
}
