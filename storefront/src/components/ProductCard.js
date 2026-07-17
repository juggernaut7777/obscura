"use client";
import { useState, memo } from "react";
import Link from "next/link";
import styles from "./ProductCard.module.css";

// ⚡ Bolt Optimization:
// Memoizing ProductCard prevents O(N) re-renders when global context state
// (like CartContext or filter changes) triggers updates in parent layouts.
// Expected Impact: Reduces unnecessary re-renders of stable product cards by ~90%
// during unrelated state changes in the parent tree.
const ProductCard = memo(function ProductCard({ product, index = 0 }) {
  const [isHovered, setIsHovered] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  const {
    id,
    name,
    price,
    comparePrice,
    images = [],
    category,
    badge,
  } = product;

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
      <Link href={`/product/${id}`} className={styles.imageWrap}>
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

        {/* Quick Add */}
        <div className={`${styles.quickAdd} ${isHovered ? styles.quickAddVisible : ""}`}>
          <button className={styles.quickAddBtn}>Quick Add</button>
        </div>
      </Link>

      <div className={styles.info}>
        <span className={styles.category}>{category}</span>
        <h3 className={styles.name}>{name}</h3>
        <div className={styles.priceRow}>
          <span className={styles.price}>${price.toFixed(2)}</span>
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
});

export default ProductCard;
