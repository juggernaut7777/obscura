"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useWishlist } from "@/context/WishlistContext";
import { useCurrency } from "@/context/CurrencyContext";
import { sound } from "@/utils/sound";
import SearchModal from "./SearchModal";
import styles from "./Header.module.css";

export default function Header({ cartCount = 0, onCartClick }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const { wishlist } = useWishlist();
  const { currency, setCurrency, currencies } = useCurrency();

  const toggleSound = () => {
    const newState = sound.toggle();
    setSoundEnabled(newState);
  };

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Cmd/Ctrl+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <div className={styles.announcementBar}>
        <span>OBSCURA ATELIER // EDITION 04 / 2026 // WORLDWIDE DDP LOGISTICS // ALL DUTIES &amp; TAXES INCLUDED</span>
      </div>
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
          <Link href="/shop" className={styles.navLink} onClick={() => setMobileOpen(false)}>Archive [Shop]</Link>
          <Link href="/lookbook" className={styles.navLink} onClick={() => setMobileOpen(false)}>Editorial</Link>
        </nav>

        {/* Logo */}
        <Link href="/" className={styles.logo}>
          <span className={styles.logoText}>O B S C U R A</span>
          <span className={styles.logoSub}>[ ARCHIVE &amp; ATELIER ]</span>
        </Link>

        {/* Right Actions */}
        <div className={styles.actions}>
          {/* Currency Selector */}
          <div className={styles.currencySelector}>
            {Object.keys(currencies).map((code) => (
              <button
                key={code}
                className={`${styles.currencyBtn} ${currency === code ? styles.currencyActive : ""}`}
                onClick={() => {
                  sound.playClick();
                  setCurrency(code);
                }}
                aria-label={`Switch currency to ${code}`}
              >
                {code}
              </button>
            ))}
          </div>

          {/* Sound Toggle */}
          <button
            className={`${styles.soundBtn} ${soundEnabled ? styles.soundActive : ""}`}
            onClick={toggleSound}
            aria-label="Toggle luxury audio feedback"
            title="Toggle tactile sound effects"
          >
            <span className={styles.soundIndicator} />
            <span className={styles.soundText}>AUDIO</span>
          </button>

          <button className={styles.actionBtn} onClick={() => { sound.playClick(); setSearchOpen(true); }} aria-label="Search (Ctrl+K)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </button>
          <Link href="/shop?wishlist=true" className={styles.actionBtn} aria-label="Wishlist" onClick={() => sound.playClick()}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill={wishlist.length > 0 ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.5">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            {wishlist.length > 0 && <span className={styles.cartBadge}>{wishlist.length}</span>}
          </Link>
          <button className={styles.actionBtn} onClick={() => { sound.playClick(); onCartClick(); }} aria-label="Cart">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <path d="M16 10a4 4 0 01-8 0"/>
            </svg>
            {cartCount > 0 && <span className={styles.cartBadge}>{cartCount}</span>}
          </button>
        </div>
      </div>
    </header>

    <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
