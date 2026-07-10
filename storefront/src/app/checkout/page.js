"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCart } from "@/context/CartContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import styles from "./page.module.css";

export default function CheckoutPage() {
  const { cartItems, clearCart } = useCart();
  const router = useRouter();
  const [step, setStep] = useState(1); // 1 = shipping, 2 = payment, 3 = success
  const [isProcessing, setIsProcessing] = useState(false);
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState("US");
  const [orderId, setOrderId] = useState("");

  const subtotal = cartItems.reduce((sum, item) => sum + item.price * item.qty, 0);
  const shipping = subtotal >= 99 ? 0 : 15;
  const total = subtotal + shipping;

  const handleSimulatePayment = async () => {
    if (!email || !firstName || !lastName || !address || !city || !postalCode) {
      alert("Please fill in all shipping fields first.");
      setStep(1);
      return;
    }

    setIsProcessing(true);
    try {
      const checkoutData = {
        customer: {
          name: `${firstName} ${lastName}`,
          email,
          address: `${address}, ${city}, ${postalCode}, ${country}`,
          country
        },
        items: cartItems.map(item => ({
          name: item.name,
          url: item.supplierLink || "https://1688.com",
          size: item.size || "OS",
          color: item.color || "Default",
          qty: item.qty,
          price_usd: item.price,
          price_cny: Math.round((item.price / 2) * 7.2), // rough approximation
          category: item.category || "clothing",
          pipeline: item.pipeline || "kakobuy"
        })),
        subtotal_usd: subtotal,
        shipping_paid_usd: shipping
      };

      const response = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(checkoutData)
      });

      const result = await response.json();
      setIsProcessing(false);

      if (result.success) {
        setOrderId(result.orderId);
        setStep(3);
        clearCart();
      } else {
        alert(`Checkout Error: ${result.error || "Failed to process order"}`);
      }
    } catch (err) {
      setIsProcessing(false);
      alert(`Checkout failed: ${err.message}`);
    }
  };

  if (step === 3) {
    return (
      <>
        <Header cartCount={0} onCartClick={() => {}} />
        <main className={styles.main}>
          <div className="container">
            <div className={styles.successBox}>
              <h1 className="heading-display">Order Confirmed.</h1>
              <p className={styles.successMsg}>
                Your order #{orderId} has been received.
                We'll email you the tracking details shortly.
              </p>
              <Link href="/shop" className="btn btn-primary">Continue Shopping</Link>
            </div>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Header cartCount={cartItems.length} onCartClick={() => router.push("/shop")} />
      <main className={styles.main}>
        <div className={`container ${styles.checkoutContainer}`}>
          
          <div className={styles.checkoutForm}>
            <h1 className="heading-display" style={{ marginBottom: "2rem" }}>Checkout</h1>
            
            {cartItems.length === 0 ? (
              <div>
                <p style={{ marginBottom: "2rem" }}>Your cart is empty.</p>
                <Link href="/shop" className="btn btn-outline">Return to Shop</Link>
              </div>
            ) : (
              <>
                {step === 1 ? (
                  <div className={styles.formSection}>
                    <h2 className={styles.sectionTitle}>Shipping Information</h2>
                    <div className={styles.inputGroup}>
                      <input 
                        type="email" 
                        placeholder="Email" 
                        className={styles.input} 
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                      />
                    </div>
                    <div className={styles.inputRow}>
                      <input 
                        type="text" 
                        placeholder="First Name" 
                        className={styles.input} 
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        required
                      />
                      <input 
                        type="text" 
                        placeholder="Last Name" 
                        className={styles.input} 
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        required
                      />
                    </div>
                    <div className={styles.inputGroup}>
                      <input 
                        type="text" 
                        placeholder="Address" 
                        className={styles.input} 
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        required
                      />
                    </div>
                    <div className={styles.inputRow}>
                      <input 
                        type="text" 
                        placeholder="City" 
                        className={styles.input} 
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        required
                      />
                      <input 
                        type="text" 
                        placeholder="Postal Code" 
                        className={styles.input} 
                        value={postalCode}
                        onChange={(e) => setPostalCode(e.target.value)}
                        required
                      />
                    </div>
                    <div className={styles.inputGroup}>
                      <select 
                        className={styles.input} 
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                        aria-label="Country"
                      >
                        <option value="US">United States</option>
                        <option value="CA">Canada</option>
                        <option value="GB">United Kingdom</option>
                        <option value="AU">Australia</option>
                        <option value="NG">Nigeria</option>
                      </select>
                    </div>
                    <button 
                      className="btn btn-primary" 
                      style={{ width: "100%", marginTop: "1rem" }}
                      onClick={() => {
                        if (!email || !firstName || !lastName || !address || !city || !postalCode) {
                          alert("Please fill in all shipping fields first.");
                          return;
                        }
                        setStep(2);
                      }}
                    >
                      Continue to Payment
                    </button>
                  </div>
                ) : (
                  <div className={styles.formSection}>
                    <h2 className={styles.sectionTitle}>Payment</h2>
                    <div className={styles.paymentMethods}>
                      <label className={styles.paymentMethod}>
                        <input type="radio" name="payment" defaultChecked />
                        <span>Credit Card</span>
                      </label>
                      <label className={styles.paymentMethod}>
                        <input type="radio" name="payment" />
                        <span>Crypto (ETH/USDC)</span>
                      </label>
                    </div>
                    
                    <div className={styles.inputGroup}>
                      <input type="text" placeholder="Card Number" className={styles.input} />
                    </div>
                    <div className={styles.inputRow}>
                      <input type="text" placeholder="MM/YY" className={styles.input} />
                      <input type="text" placeholder="CVC" className={styles.input} />
                    </div>

                    <div className={styles.actionRow}>
                      <button className="btn btn-ghost" onClick={() => setStep(1)}>
                        ← Back to Shipping
                      </button>
                      <button 
                        className="btn btn-primary" 
                        onClick={handleSimulatePayment}
                        disabled={isProcessing}
                      >
                        {isProcessing ? "Processing..." : `Pay $${total.toFixed(2)}`}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {cartItems.length > 0 && (
            <div className={styles.orderSummary}>
              <h3 className={styles.summaryTitle}>Order Summary</h3>
              <div className={styles.itemsList}>
                {cartItems.map((item) => (
                  <div key={item.id} className={styles.summaryItem}>
                    <img src={item.image} alt={item.name} className={styles.itemImg} />
                    <div className={styles.itemInfo}>
                      <div className={styles.itemName}>{item.name}</div>
                      <div className={styles.itemMeta}>
                        {item.size && `Size: ${item.size}`} {item.color && `| Color: ${item.color}`}
                      </div>
                      <div className={styles.itemQty}>Qty: {item.qty}</div>
                    </div>
                    <div className={styles.itemPrice}>${(item.price * item.qty).toFixed(2)}</div>
                  </div>
                ))}
              </div>
              
              <div className={styles.totals}>
                <div className={styles.totalRow}>
                  <span>Subtotal</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                <div className={styles.totalRow}>
                  <span>Shipping</span>
                  <span>{shipping === 0 ? "FREE" : `$${shipping.toFixed(2)}`}</span>
                </div>
                <div className={`${styles.totalRow} ${styles.grandTotal}`}>
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </>
  );
}
