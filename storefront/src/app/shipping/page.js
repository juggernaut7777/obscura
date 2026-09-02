"use client";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useCart } from "@/context/CartContext";
import styles from "./page.module.css";

const SHIPPING_ZONES = [
  { zone: "United States", method: "Standard Air", time: "10–14 business days", cost: "$15 flat rate" },
  { zone: "Canada", method: "Standard Air", time: "12–16 business days", cost: "$15 flat rate" },
  { zone: "United Kingdom", method: "International Air", time: "14–18 business days", cost: "$18 flat rate" },
  { zone: "Europe", method: "International Air", time: "14–20 business days", cost: "$18 flat rate" },
  { zone: "Nigeria", method: "DDP Air Cargo", time: "12–18 business days", cost: "Calculated at checkout" },
  { zone: "South Africa", method: "DDP Air Cargo", time: "14–20 business days", cost: "Calculated at checkout" },
  { zone: "Rest of World", method: "International Air", time: "18–25 business days", cost: "$22 flat rate" },
];

export default function ShippingPage() {
  const { cartItems, setCartOpen } = useCart();

  return (
    <>
      <Header cartCount={cartItems.length} onCartClick={() => setCartOpen(true)} />
      <main className={styles.main}>
        <div className={styles.hero}>
          <span className={styles.label}>Logistics</span>
          <h1 className={styles.title}>Shipping & Delivery</h1>
          <p className={styles.subtitle}>
            We ship worldwide — directly from our curated atelier partners. Here&apos;s everything you need to know.
          </p>
        </div>

        <div className={styles.content}>
          {/* Free Shipping Banner */}
          <div className={styles.banner}>
            <span className={styles.bannerIcon}>✦</span>
            <div>
              <strong>Free Shipping on Orders Over $200</strong>
              <p>All qualifying orders ship free via standard air freight.</p>
            </div>
          </div>

          {/* Shipping Zones Table */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Shipping Zones</h2>
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Destination</th>
                    <th>Method</th>
                    <th>Estimated Delivery</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {SHIPPING_ZONES.map((zone) => (
                    <tr key={zone.zone}>
                      <td>{zone.zone}</td>
                      <td>{zone.method}</td>
                      <td>{zone.time}</td>
                      <td className={styles.cost}>{zone.cost}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Order Tracking */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Order Tracking</h2>
            <div className={styles.infoCard}>
              <p>Once your order ships, you&apos;ll receive a tracking number via email within 3–5 business days. Track your package through our logistics partner&apos;s portal.</p>
              <p>Processing time is typically 2–4 business days before shipment. During high-demand drops, allow an additional 1–2 days.</p>
            </div>
          </section>

          {/* Customs */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Customs & Import Duties</h2>
            <div className={styles.infoCard}>
              <p>International orders may be subject to customs duties, import taxes, and fees levied by your country&apos;s government. These charges are <strong>not included</strong> in our prices and are the responsibility of the buyer.</p>
              <p>For African destinations, we use DDP (Delivered Duty Paid) shipping where all customs and taxes are included in the shipping cost shown at checkout.</p>
            </div>
          </section>

          {/* Processing Times */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Processing Timeline</h2>
            <div className={styles.timeline}>
              <div className={styles.timelineStep}>
                <div className={styles.stepNumber}>1</div>
                <div>
                  <strong>Order Confirmed</strong>
                  <p>Payment verified, order enters fulfillment queue</p>
                </div>
              </div>
              <div className={styles.timelineStep}>
                <div className={styles.stepNumber}>2</div>
                <div>
                  <strong>Processing</strong>
                  <p>2–4 business days — quality check and packaging</p>
                </div>
              </div>
              <div className={styles.timelineStep}>
                <div className={styles.stepNumber}>3</div>
                <div>
                  <strong>Shipped</strong>
                  <p>Tracking number sent to your email</p>
                </div>
              </div>
              <div className={styles.timelineStep}>
                <div className={styles.stepNumber}>4</div>
                <div>
                  <strong>Delivered</strong>
                  <p>Package arrives at your door</p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </>
  );
}
