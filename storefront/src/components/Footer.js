import Link from "next/link";
import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        {/* Brand */}
        <div className={styles.brand}>
          <div className={styles.logo}>
            <span className={styles.logoText}>OBSCURA</span>
            <span className={styles.logoSub}>GARMENTS</span>
          </div>
          <p className={styles.tagline}>
            Curated fashion for the aesthetically inclined. 
            Every piece handpicked, every detail intentional.
          </p>
        </div>

        {/* Links */}
        <div className={styles.links}>
          <div className={styles.col}>
            <h4 className={styles.colTitle}>Company</h4>
            <ul className={styles.linkList}>
              <li><Link href="/">Home</Link></li>
              <li><Link href="/shop">Shop</Link></li>
              <li><Link href="/shop/outfits">Outfits</Link></li>
            </ul>
          </div>
          <div className={styles.col}>
            <h4 className={styles.colTitle}>Support</h4>
            <ul className={styles.linkList}>
              <li><Link href="mailto:support@obscuragarments.com">Contact Us</Link></li>
              <li><Link href="/">FAQ</Link></li>
            </ul>
          </div>
          <div className={styles.linkGroup}>
            <h4 className={styles.groupTitle}>Connect</h4>
            <a href="https://instagram.com" target="_blank" rel="noopener noreferrer">Instagram</a>
            <a href="https://tiktok.com" target="_blank" rel="noopener noreferrer">TikTok</a>
            <a href="https://pinterest.com" target="_blank" rel="noopener noreferrer">Pinterest</a>
          </div>
        </div>
      </div>

      {/* Bottom */}
      <div className={styles.bottom}>
        <div className="container">
          <p>&copy; {new Date().getFullYear()} Obscura Garments. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
