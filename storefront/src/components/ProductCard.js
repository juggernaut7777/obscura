"use client";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useWishlist } from "@/context/WishlistContext";
import { useCurrency } from "@/context/CurrencyContext";
import { useCart } from "@/context/CartContext";
import { sound } from "@/utils/sound";
import styles from "./ProductCard.module.css";

export default function ProductCard({ product, index = 0 }) {
  const [isHovered, setIsHovered] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [addedSize, setAddedSize] = useState(null);
  const imgRef = useRef(null);

  const { isWishlisted, toggleWishlist } = useWishlist();
  const { formatPrice } = useCurrency();
  const { addToCart } = useCart();

  const {
    id,
    name,
    price,
    comparePrice,
    images = [],
    category,
    badge,
    colors = [],
    brand = "",
    videoUrl,
    weightGsm,
    sizes = ["S", "M", "L", "XL"]
  } = product;

  const wishlisted = isWishlisted(id);

  const handleQuickAdd = (e, size) => {
    e.preventDefault();
    e.stopPropagation();
    sound.playChime();
    addToCart({
      ...product,
      id: `${id}-${size.toLowerCase()}`,
      productId: id,
      size,
      image: primaryImage
    }, 1);
    setAddedSize(size);
    setTimeout(() => setAddedSize(null), 2200);
  };

  // Luxury standard: Card images must be clean garment views, never selfies, mirrors, or talking-head clips
  const cleanImages = images.filter(img => {
    if (!img) return false;
    const l = img.toLowerCase();
    return !l.includes("selfie") && 
           !l.includes("mirror") && 
           !l.includes("face") && 
           !l.includes("tiktokad") && 
           !l.includes("josh");
  });

  const primaryImage = cleanImages[0] || images[0] || "/images/main_hero_bg.jpg";
  
  // Hover angle: strictly prefer garment back flat lay or fabric detail
  const backGarment = cleanImages.find(img => 
    img !== primaryImage && 
    (img.toLowerCase().includes("back") || 
     img.toLowerCase().includes("flat_lay") || 
     img.toLowerCase().includes("detail") ||
     img.toLowerCase().includes("default_2.jpg") ||
     img.toLowerCase().includes("default_3.jpg")) &&
    !img.toLowerCase().includes("model")
  );

  // If no back garment exists, keep primaryImage (smooth scale transition, no face swap)
  const hoverImage = backGarment || primaryImage;
  const discount = comparePrice
    ? Math.round(((comparePrice - price) / comparePrice) * 100)
    : 0;

  useEffect(() => {
    if (imgRef.current && imgRef.current.complete && imgRef.current.naturalWidth > 0) {
      setImageLoaded(true);
    }
  }, [primaryImage]);


  return (
    <div
      className={`${styles.card} animate-fade-in-up delay-${(index % 4) + 1}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={styles.imageWrap}>
        {/* Wishlist Button */}
        <button
          className={`${styles.wishlistBtn} ${wishlisted ? styles.wishlisted : ""}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            toggleWishlist(id);
          }}
          aria-label={wishlisted ? "Remove from wishlist" : "Add to wishlist"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill={wishlisted ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.5">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>

        <Link href={`/product/${id}`}>
          {/* Loading shimmer */}
          {!imageLoaded && <div className={styles.shimmer} />}

          {/* Primary Garment Image */}
          <img
            ref={imgRef}
            src={primaryImage}
            alt={name}
            className={`${styles.image} ${isHovered && hoverImage !== primaryImage ? styles.imageHidden : ""}`}
            onLoad={() => setImageLoaded(true)}
            onError={(e) => {
              setImageLoaded(true);
              if (!e.currentTarget.src.includes("main_hero_bg") && !e.currentTarget.src.includes("editorial_hero")) {
                e.currentTarget.src = "/images/main_hero_bg.jpg";
              }
            }}
            loading="lazy"
          />

          {/* Alternate Angle on Hover (Back or Detail) */}
          {hoverImage !== primaryImage && (
            <img
              src={hoverImage}
              alt={`${name} alternate angle`}
              className={`${styles.image} ${styles.imageHover} ${isHovered ? styles.imageVisible : ""}`}
              onError={(e) => {
                e.currentTarget.src = primaryImage;
              }}
              loading="lazy"
            />
          )}


          {/* Architectural Badges */}
          <div style={{ position: "absolute", top: "10px", left: "10px", display: "flex", flexDirection: "column", gap: "6px", zIndex: 3 }}>
            {badge && <span className={styles.badge}>{badge}</span>}
            {videoUrl && (
              <span className={styles.motionTag}>
                <svg width="8" height="8" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                9:16 MOTION
              </span>
            )}
          </div>

          {/* Quick View & Quick Size Overlay */}
          <div className={`${styles.quickAdd} ${isHovered ? styles.quickAddVisible : ""}`}>
            {addedSize ? (
              <span className={styles.addedBadge}>
                [ ALLOCATED SIZE {addedSize} TO BAG ✓ ]
              </span>
            ) : (
              <div className={styles.quickSizeContainer}>
                <span className={styles.quickSizeLabel}>[ QUICK ALLOCATE ]</span>
                <div className={styles.sizePills}>
                  {sizes.slice(0, 5).map((s) => (
                    <button
                      key={s}
                      type="button"
                      className={styles.sizePillBtn}
                      onClick={(e) => handleQuickAdd(e, s)}
                      title={`Quick add size ${s}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Link>
      </div>

      <div className={styles.info}>
        <div className={styles.metaRow}>
          <span className={styles.category}>{brand ? `${brand} // ${category}` : category}</span>
          {weightGsm ? (
            <span className={styles.gsmTag}>[{weightGsm} GSM]</span>
          ) : colors.length > 1 ? (
            <span className={styles.colorCount}>[{colors.length} VARIANTS]</span>
          ) : null}
        </div>
        
        <Link href={`/product/${id}`} className={styles.nameLink}>
          <h3 className={styles.name}>{name}</h3>
        </Link>
        
        {/* Color Dots Preview */}
        {colors.length > 0 && (
          <div className={styles.colorDots}>
            {colors.slice(0, 6).map((c, i) => {
              const hex = typeof c === "object" ? c.hex : "#888888";
              return (
                <span
                  key={i}
                  className={styles.colorDot}
                  style={{ backgroundColor: hex }}
                  title={typeof c === "object" ? c.name : c}
                />
              );
            })}
            {colors.length > 6 && (
              <span className={styles.colorMore}>+{colors.length - 6}</span>
            )}
          </div>
        )}

        <div className={styles.priceRow}>
          <span className={styles.price}>{formatPrice(price)}</span>
          {comparePrice > 0 && (
            <span className={styles.comparePrice}>{formatPrice(comparePrice)}</span>
          )}
        </div>
      </div>
    </div>
  );
}
