"use client";
import styles from "./CartSidebar.module.css";
import Link from "next/link";
import { WEIGHT_BY_CATEGORY } from "../constants/weights";

function getItemWeight(item) {
  const cat = (item.category || item.subCategory || "default").toLowerCase();
  for (const [key, weight] of Object.entries(WEIGHT_BY_CATEGORY)) {
    if (cat.includes(key)) return weight * (item.qty || 1);
  }
  return WEIGHT_BY_CATEGORY.default * (item.qty || 1);
}

// Simple flat rate shipping with free threshold at $200
function calcShipping(totalWeightKg, subtotal) {
  if (subtotal >= 200) return { fee: 0,     label: "FREE",    note: "Free shipping on orders over $200" };
  return                     { fee: 15,    label: "$15.00",  note: "Standard delivery · 7-15 days" };
}

export default function CartSidebar({ isOpen, onClose, items = [], onUpdateQty, onRemove }) {
  const subtotal = items.reduce((sum, item) => sum + item.price * (item.qty || 1), 0);
  const totalWeight = items.reduce((sum, item) => sum + getItemWeight(item), 0);
  const shipping = calcShipping(totalWeight, subtotal);
  const total = subtotal + shipping.fee;

  // Detect mixed pipeline orders (multiple shipping origins = 2 packages)
  const hasMixed = items.some(i => i.pipeline === "cj") && items.some(i => i.pipeline !== "cj");

  return (
    <>
      {/* Backdrop */}
      <div
        className={`${styles.backdrop} ${isOpen ? styles.backdropOpen : ""}`}
        onClick={onClose}
      />

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${isOpen ? styles.sidebarOpen : ""}`}>
        {/* Header */}
        <div className={styles.header}>
          <h2 className={styles.title}>Your Bag</h2>
          <span className={styles.count}>{items.length} {items.length === 1 ? 'item' : 'items'}</span>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close cart">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Items */}
        <div className={styles.items}>
          {items.length === 0 ? (
            <div className={styles.empty}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.3">
                <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/>
                <line x1="3" y1="6" x2="21" y2="6"/>
                <path d="M16 10a4 4 0 01-8 0"/>
              </svg>
              <p className={styles.emptyText}>Your bag is empty</p>
              <button className="btn btn-outline" onClick={onClose}>Continue Shopping</button>
            </div>
          ) : (
            items.map((item) => (
              <div key={item.id} className={styles.item}>
                <div className={styles.itemImage}>
                  <img src={item.image} alt={item.name} />
                </div>
                <div className={styles.itemInfo}>
                  <h4 className={styles.itemName}>{item.name}</h4>
                  {item.size && <span className={styles.itemSize}>Size: {item.size}</span>}
                  {item.color && <span className={styles.itemSize}>Colour: {item.color}</span>}
                  <div className={styles.itemBottom}>
                    <div className={styles.qtyControl}>
                      <button onClick={() => onUpdateQty(item.id, (item.qty || 1) - 1)}>−</button>
                      <span>{item.qty || 1}</span>
                      <button onClick={() => onUpdateQty(item.id, (item.qty || 1) + 1)}>+</button>
                    </div>
                    <span className={styles.itemPrice}>${(item.price * (item.qty || 1)).toFixed(2)}</span>
                  </div>
                </div>
                <button className={styles.removeBtn} onClick={() => onRemove(item.id)} aria-label="Remove item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M18 6L6 18M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className={styles.footer}>
            <div className={styles.subtotalRow}>
              <span>Subtotal</span>
              <span className={styles.subtotalPrice}>${subtotal.toFixed(2)}</span>
            </div>
            <div className={styles.subtotalRow}>
              <span>
                Shipping{" "}
                <span style={{ fontSize: "0.7rem", opacity: 0.5 }}>~{totalWeight.toFixed(2)}kg</span>
              </span>
              <span
                className={styles.subtotalPrice}
                style={{ color: shipping.fee === 0 ? "#a8e6cf" : "inherit" }}
              >
                {shipping.label}
              </span>
            </div>
            <p
              className={styles.shippingNote}
              style={{ color: shipping.fee === 0 ? "#a8e6cf" : "rgba(255,255,255,0.5)" }}
            >
              {shipping.note}
            </p>
            {hasMixed && (
              <p className={styles.shippingNote} style={{ color: "#f4c56a", marginTop: "4px" }}>
                📦 Mixed order — ships in 2 packages
              </p>
            )}
            {shipping.fee > 0 && subtotal < 200 && (
              <p className={styles.shippingNote} style={{ color: "#a8e6cf" }}>
                🎁 Add ${(200 - subtotal).toFixed(0)} more for FREE shipping
              </p>
            )}
            <div
              className={styles.subtotalRow}
              style={{
                borderTop: "1px solid rgba(255,255,255,0.1)",
                paddingTop: "8px",
                marginTop: "4px",
              }}
            >
              <span style={{ fontWeight: 600 }}>Total</span>
              <span className={styles.subtotalPrice} style={{ fontWeight: 600 }}>
                ${total.toFixed(2)}
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "12px" }}>
              <Link href="/checkout" className="btn btn-primary" style={{ width: "100%", textAlign: "center" }} onClick={onClose}>
                Checkout — ${total.toFixed(2)}
              </Link>
              <Link
                href="/checkout"
                className="btn btn-outline"
                style={{ width: "100%", borderColor: "#a8e6cf", color: "#a8e6cf", textAlign: "center" }}
                onClick={onClose}
              >
                Pay with Crypto (USDC/USDT)
              </Link>
            </div>
            <p className={styles.shippingNote} style={{ marginTop: "8px", fontSize: "0.7rem" }}>
              Worldwide shipping · Tracked delivery
            </p>
          </div>
        )}
      </aside>
    </>
  );
}
