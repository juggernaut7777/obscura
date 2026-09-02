import Link from "next/link";
import styles from "./Footer.module.css";

const InstagramIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
  </svg>
);

const TikTokIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5"></path>
  </svg>
);

const PinterestIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="22" x2="12" y2="10"></line>
    <path d="M12 2a5 5 0 0 0-5 5c0 2 1.5 3.5 1.5 3.5s-.5 2-1 4.5c-.3 1.5-1 3.5-1 3.5s1-.5 1.5-2c.3-1 .5-2 1-3.5 1.5.5 3.5 0 3.5-2.5 0-3-2.5-4-5-4s-5 1.5-5 4c0 1.5.5 3.5.5 3.5s-.5 1.5-1 4"></path>
  </svg>
);

const VisaIcon = () => (
  <svg viewBox="0 0 38 24" width="38" height="24" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="pi-visa"><title id="pi-visa">Visa</title><path opacity=".07" d="M35 0H3C1.3 0 0 1.3 0 3v18c0 1.7 1.4 3 3 3h32c1.7 0 3-1.3 3-3V3c0-1.7-1.4-3-3-3z"/><path fill="#fff" d="M35 1c1.1 0 2 .9 2 2v18c0 1.1-.9 2-2 2H3c-1.1 0-2-.9-2-2V3c0-1.1.9-2 2-2h32"/><path d="M28.3 10.1c-.2-.1-1.4-.4-3.1-.4-3.6 0-6.1 2-6.1 4.8 0 2.1 1.9 3.2 3.3 3.9 1.4.7 1.9 1.1 1.9 1.8 0 1-1.2 1.5-2.4 1.5-1.9 0-3-.3-4-.7l-.6-.3-.6 3.6c1 .5 2.8.9 4.6.9 3.8 0 6.3-1.9 6.3-4.9 0-2.6-3.6-2.7-3.6-3.9 0-.6.6-1.2 2-1.3 1.1-.1 2.5.2 3.6.7l.5.2.6-3.9zM15 10.2h-3.6c-.6 0-1.2.2-1.4.9l-5.3 12.6h4.3l.9-2.4h5.2l.5 2.4h4L15 10.2zm-2.4 8.2l2-5.4h.1l1 5.4h-3.1zm11.9-8.2h-4l-2.4 14.8h3.9l2.5-14.8zm-16-3.2L7 13.9 6.3 11c-.3-1.3-1.7-2.6-3.2-3.3l2.2 14.8h4.2l6.5-14.8h-4.2zM2.8 10.4c-1.1-.2-2.1-.2-3.1-.1l.1 1.5c1.8 0 3.5.3 5.4.9l-.7-2.3z" fill="#1434CB"/></svg>
);

const MastercardIcon = () => (
  <svg viewBox="0 0 38 24" width="38" height="24" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="pi-master"><title id="pi-master">Mastercard</title><path opacity=".07" d="M35 0H3C1.3 0 0 1.3 0 3v18c0 1.7 1.4 3 3 3h32c1.7 0 3-1.3 3-3V3c0-1.7-1.4-3-3-3z"/><path fill="#fff" d="M35 1c1.1 0 2 .9 2 2v18c0 1.1-.9 2-2 2H3c-1.1 0-2-.9-2-2V3c0-1.1.9-2 2-2h32"/><circle fill="#EB001B" cx="15" cy="12" r="7"/><circle fill="#F79E1B" cx="23" cy="12" r="7"/><path fill="#FF5F00" d="M22 12c0-2.4-1.2-4.5-3-5.7-1.8 1.3-3 3.4-3 5.7s1.2 4.5 3 5.7c1.8-1.2 3-3.3 3-5.7z"/></svg>
);

const ApplePayIcon = () => (
  <svg viewBox="0 0 38 24" width="38" height="24" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="pi-apple-pay"><title id="pi-apple-pay">Apple Pay</title><path opacity=".07" d="M35 0H3C1.3 0 0 1.3 0 3v18c0 1.7 1.4 3 3 3h32c1.7 0 3-1.3 3-3V3c0-1.7-1.4-3-3-3z"/><path fill="#fff" d="M35 1c1.1 0 2 .9 2 2v18c0 1.1-.9 2-2 2H3c-1.1 0-2-.9-2-2V3c0-1.1.9-2 2-2h32"/><path d="M17.3 12.2c0-1.9 1.5-2.8 1.5-2.8-.9-1.3-2.3-1.5-2.8-1.5-1.2-.1-2.4.7-3 .7-.6 0-1.5-.7-2.6-.7-1.3 0-2.6.8-3.3 2.1-1.4 2.4-.4 6 1 8 1 1.4 2 3 3.5 2.9 1.4-.1 1.9-.9 3.5-.9 1.6 0 2.1.9 3.6.9 1.5.1 2.5-1.5 3.4-2.9.9-1.4 1.3-2.8 1.3-2.8-.1 0-2.5-1-2.5-3.8zM15 7.1c.8-1 1.3-2.4 1.1-3.7-1.1.1-2.6.7-3.4 1.7-.7.8-1.3 2.2-1.1 3.6 1.2.1 2.6-.6 3.4-1.6z" fill="#000"/></svg>
);

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.topGradient}></div>
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
          <div className={styles.linkGroup}>
            <h4 className={styles.groupTitle}>Company</h4>
            <ul className={styles.linkList}>
              <li><Link href="/">Home</Link></li>
              <li><Link href="/shop">Shop</Link></li>
              <li><Link href="/lookbook">Lookbook</Link></li>
            </ul>
          </div>
          <div className={styles.linkGroup}>
            <h4 className={styles.groupTitle}>Support</h4>
            <ul className={styles.linkList}>
              <li><Link href="mailto:support@obscuragarments.com">Contact Us</Link></li>
              <li><Link href="/faq">FAQ</Link></li>
              <li><Link href="/shipping">Shipping &amp; Returns</Link></li>
            </ul>
          </div>
          <div className={styles.linkGroup}>
            <h4 className={styles.groupTitle}>Connect</h4>
            <div className={styles.socials}>
              <a href="https://instagram.com/obscuragarments" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
                <InstagramIcon />
              </a>
              <a href="https://tiktok.com/@obscuragarments" target="_blank" rel="noopener noreferrer" aria-label="TikTok">
                <TikTokIcon />
              </a>
              <a href="https://pinterest.com/obscuragarments" target="_blank" rel="noopener noreferrer" aria-label="Pinterest">
                <PinterestIcon />
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom */}
      <div className={styles.bottom}>
        <div className={`container ${styles.bottomInner}`}>
          <p>&copy; {new Date().getFullYear()} Obscura Garments. All rights reserved.</p>
          <div className={styles.paymentMethods}>
            <VisaIcon />
            <MastercardIcon />
            <ApplePayIcon />
          </div>
        </div>
      </div>
    </footer>
  );
}
