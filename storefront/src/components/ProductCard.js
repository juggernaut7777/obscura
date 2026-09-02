"use client";
import { useState } from "react";
import Link from "next/link";
import { useWishlist } from "@/context/WishlistContext";
import styles from "./ProductCard.module.css";

export default function ProductCard({ product, index = 0 }) {
  const [isHovered, setIsHovered] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const { isWishlisted, toggleWishlist } = useWishlist();

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
  } = product;

  const wishlisted = isWishlisted(id);

  const primaryImage = images[0] || "/placeholder.jpg";
  const hoverImage = images[1] || primaryImage;
  const discount = comparePrice
    ? Math.round(((comparePrice - price) / comparePrice) * 100)
    : 0;

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

          {/* Primary Image */}
          <img
            src={primaryImage}
            alt={name}
            className={`${styles.image} ${isHovered ? styles.imageHidden : ""}`}
            onLoad={() => setImageLoaded(true)}
            loading="lazy"
          />

          {/* Hover Image */}
          {images.length > 1 && (
            <img
              src={hoverImage}
              alt={`${name} alternate view`}
              className={`${styles.image} ${styles.imageHover} ${isHovered ? styles.imageVisible : ""}`}
              loading="lazy"
            />
          )}

          {/* Badge */}
          {badge && <span className={styles.badge}>{badge}</span>}

          {/* Quick View */}
          <div className={`${styles.quickAdd} ${isHovered ? styles.quickAddVisible : ""}`}>
            <span className={styles.quickAddBtn}>View Piece →</span>
          </div>
        </Link>
      </div>

      <div className={styles.info}>
        <div className={styles.metaRow}>
          <span className={styles.category}>{brand ? `${brand} · ${category}` : category}</span>
          {colors.length > 1 && (
            <span className={styles.colorCount}>{colors.length} Colors</span>
          )}
        </div>
        
        <Link href={`/product/${id}`}>
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
          <span className={styles.price}>${price.toFixed(2)} USD</span>
          {comparePrice > 0 && (
            <>
              <span className={styles.comparePrice}>${comparePrice.toFixed(2)}</span>
              <span className={styles.discount}>-{discount}%</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
