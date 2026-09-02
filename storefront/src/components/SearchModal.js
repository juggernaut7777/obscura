"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { DEMO_PRODUCTS } from "@/data/products";
import styles from "./SearchModal.module.css";

export default function SearchModal({ isOpen, onClose }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const inputRef = useRef(null);
  const router = useRouter();

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setResults([]);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleSearch = useCallback((value) => {
    setQuery(value);
    if (!value.trim()) {
      setResults([]);
      return;
    }
    const q = value.toLowerCase();
    const filtered = DEMO_PRODUCTS.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.category?.toLowerCase().includes(q) ||
        p.description?.toLowerCase().includes(q) ||
        p.brand?.toLowerCase().includes(q)
    );
    setResults(filtered);
  }, []);

  const handleSelect = (productId) => {
    onClose();
    router.push(`/product/${productId}`);
  };

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.searchBar}>
          <svg className={styles.searchIcon} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            ref={inputRef}
            className={styles.input}
            type="text"
            placeholder="Search pieces, collections..."
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
          />
          <div className={styles.shortcut}>
            <kbd className={styles.kbd}>ESC</kbd>
          </div>
        </div>

        <div className={styles.results}>
          {query && results.length === 0 && (
            <div className={styles.empty}>
              <span className={styles.emptyIcon}>&#10022;</span>
              <p>No pieces found for &ldquo;{query}&rdquo;</p>
              <span className={styles.emptyHint}>Try a different search term</span>
            </div>
          )}

          {results.map((product) => (
            <button
              key={product.id}
              className={styles.resultItem}
              onClick={() => handleSelect(product.id)}
            >
              <div className={styles.resultImage}>
                <img
                  src={product.images?.[0] || "/placeholder.jpg"}
                  alt={product.name}
                />
              </div>
              <div className={styles.resultInfo}>
                <span className={styles.resultCategory}>{product.category}</span>
                <span className={styles.resultName}>{product.name}</span>
                <div className={styles.resultPrice}>
                  <span>${product.price}</span>
                  {product.comparePrice && (
                    <span className={styles.comparePrice}>${product.comparePrice}</span>
                  )}
                </div>
              </div>
              <svg className={styles.resultArrow} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </button>
          ))}

          {!query && (
            <div className={styles.empty}>
              <span className={styles.emptyIcon}>&#8984;</span>
              <p>Start typing to search</p>
              <span className={styles.emptyHint}>Search by name, category, or description</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
