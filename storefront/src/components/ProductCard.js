"use client";
import { useState } from "react";
import Link from "next/link";
import styles from "./ProductCard.module.css";
import { useCart } from "../context/CartContext";

export default function ProductCard({ product, index = 0 }) {
  const [isHovered, setIsHovered] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const { addToCart, setIsSidebarOpen } = useCart();

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

  const handleAddToCart = (e) => {
    e.preventDefault(); // Prevent navigating to the product page
    addToCart(product);
    setIsSidebarOpen(true);
  };

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
          <button className={styles.quickAddBtn} onClick={handleAddToCart}>Quick Add</button>
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
}
