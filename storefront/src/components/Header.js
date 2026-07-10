"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import styles from "./Header.module.css";

export default function Header({ cartCount = 0, onCartClick }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ""}`}>
      <div className={styles.inner}>
        {/* Mobile Menu Toggle */}
        <button
          className={styles.menuBtn}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <span className={`${styles.menuLine} ${mobileOpen ? styles.open : ""}`} />
          <span className={`${styles.menuLine} ${mobileOpen ? styles.open : ""}`} />
        </button>

        {/* Navigation */}
        <nav className={`${styles.nav} ${mobileOpen ? styles.navOpen : ""}`}>
          <Link href="/shop" className={styles.navLink} onClick={() => setMobileOpen(false)}>Shop</Link>
          <Link href="/lookbook" className={styles.navLink} onClick={() => setMobileOpen(false)}>Lookbook</Link>
        </nav>

        {/* Logo */}
        <Link href="/" className={styles.logo}>
          <span className={styles.logoText}>OBSCURA</span>
          <span className={styles.logoSub}>GARMENTS</span>
        </Link>

        {/* Right Actions */}
        <div className={styles.actions}>
          <Link href="/shop" className={styles.actionBtn} aria-label="Search">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </Link>
          <button className={styles.actionBtn} onClick={onCartClick} aria-label="Cart">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <path d="M16 10a4 4 0 01-8 0"/>
            </svg>
            {cartCount > 0 && <span className={styles.cartBadge}>{cartCount}</span>}
          </button>
        </div>
      </div>
    </header>
  );
}
