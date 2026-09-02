"use client";
import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCart } from "@/context/CartContext";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import { DEMO_PRODUCTS as products } from "@/data/products";
import styles from "./page.module.css";

function CheckoutContent() {
  const { cartItems, addToCart, clearCart, updateQty, removeFromCart } = useCart();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [step, setStep] = useState(1); // 1 = shipping, 2 = payment, 3 = success
  const [paymentMethod, setPaymentMethod] = useState("paystack"); // paystack, crypto, card
  const [selectedCurrency, setSelectedCurrency] = useState("NGN"); // NGN, GHS, ZAR, KES, USD
  const [selectedCryptoNetwork, setSelectedCryptoNetwork] = useState("USDT_TRC20"); // USDT_TRC20, USDT_BEP20, SOL, ETH
  const [txHash, setTxHash] = useState("");
  const [copied, setCopied] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);

  // Form Fields
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState("NG");
  const [orderId, setOrderId] = useState("");
  const [paymentDetails, setPaymentDetails] = useState(null);

  // 1. Auto-handle DM-to-Order links (?dm_order=true&product=...&color=...&size=...)
  useEffect(() => {
    const isDm = searchParams.get("dm_order");
    const productId = searchParams.get("product");
    const color = searchParams.get("color") || "Black";
    const size = searchParams.get("size") || "L";
    const pay = searchParams.get("pay");
    const curr = searchParams.get("curr");

    if (isDm && productId) {
      const match = products.find(p => p.id === productId || p.name.toLowerCase().includes(productId.toLowerCase()));
      if (match) {
        addToCart(match, color, size, 1);
        if (pay) setPaymentMethod(pay);
        if (curr) setSelectedCurrency(curr);
      }
    }
  }, [searchParams]);

  // Crypto Treasury Wallet Addresses
  const CRYPTO_WALLETS = {
    USDT_TRC20: {
      network: "TRON (TRC20)",
      symbol: "USDT",
      address: "TX9Kz8g5R4P2mN7vQ1wL9yE3H6jF0bC4aS",
      qr: "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=TX9Kz8g5R4P2mN7vQ1wL9yE3H6jF0bC4aS"
    },
    USDT_BEP20: {
      network: "BNB Smart Chain (BEP20)",
      symbol: "USDT",
      address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
      qr: "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    },
    SOL: {
      network: "Solana (SOL)",
      symbol: "SOL",
      address: "7xKXtg2CW87d97TXwSDPjN5w4P5sB4sE2q1v3W9yZ8mK",
      qr: "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=7xKXtg2CW87d97TXwSDPjN5w4P5sB4sE2q1v3W9yZ8mK"
    },
    ETH: {
      network: "Ethereum (ERC20)",
      symbol: "ETH / USDC",
      address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
      qr: "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
    }
  };

  const EXCHANGE_RATES = {
    USD: 1.0,
    NGN: 1500.0,
    GHS: 15.5,
    ZAR: 18.5,
    KES: 130.0
  };

  const subtotal = cartItems.reduce((sum, item) => sum + item.price * item.qty, 0);
  const shipping = subtotal >= 200 ? 0 : 15;
  const totalUsd = subtotal + shipping;

  const currentRate = EXCHANGE_RATES[selectedCurrency] || 1500.0;
  const totalLocal = totalUsd * currentRate;

  const handleCopyAddress = (addr) => {
    navigator.clipboard.writeText(addr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCompleteOrder = async () => {
    if (!email || !firstName || !lastName || !address || !city || !postalCode) {
      alert("Please fill in all shipping fields first.");
      setStep(1);
      return;
    }

    if (paymentMethod === "crypto" && !txHash) {
      alert("Please enter your transaction TxID / Hash after sending crypto.");
      return;
    }

    setIsProcessing(true);

    try {
      // 1. Initialize Paystack if selected
      let paystackRes = null;
      if (paymentMethod === "paystack") {
        const pRes = await fetch("/api/paystack", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "initialize",
            email,
            amount_usd: totalUsd,
            currency: selectedCurrency
          })
        });
        paystackRes = await pRes.json();
      }

      // 2. Process Order via Order Fulfillment Engine
      const checkoutData = {
        customer: {
          name: `${firstName} ${lastName}`,
          email,
          address: `${address}, ${city}, ${postalCode}, ${country}`,
          country
        },
        items: cartItems.map(item => ({
          name: item.name,
          size: item.size || "OS",
          color: item.color || "Default",
          qty: item.qty,
          price_usd: item.price,
          category: item.category || "clothing"
        })),
        subtotal_usd: subtotal,
        shipping_paid_usd: shipping,
        payment: {
          method: paymentMethod,
          currency: selectedCurrency,
          local_amount: totalLocal,
          paystack: paystackRes,
          crypto_tx: txHash || null
        }
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
        setPaymentDetails({
          paystack: paystackRes,
          crypto: paymentMethod === "crypto" ? CRYPTO_WALLETS[selectedCryptoNetwork] : null
        });
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
        <Header cartCount={0} onCartClick={() => setCartOpen(true)} />
        <main className={styles.main}>
          <div className="container">
            <div className={styles.successBox}>
              <h1 className="heading-display">Order Confirmed.</h1>
              <p className={styles.successMsg}>
                Your order <strong>#{orderId}</strong> has been received and routed to our fulfillment pipeline.
                We'll email tracking updates to <strong>{email}</strong>.
              </p>

              {paymentDetails?.paystack?.authorization_url && (
                <div style={{ margin: "2rem 0" }}>
                  <a 
                    href={paymentDetails.paystack.authorization_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                  >
                    Complete Payment via Paystack Gateway →
                  </a>
                </div>
              )}

              <Link href="/shop" className="btn btn-outline" style={{ marginTop: "1rem" }}>Continue Shopping</Link>
            </div>
          </div>
        </main>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Header cartCount={cartItems.length} onCartClick={() => setCartOpen(true)} />
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
                    <h2 className={styles.sectionTitle}>1. Shipping Information</h2>
                    <div className={styles.inputGroup}>
                      <input 
                        type="email" 
                        placeholder="Email Address" 
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
                        placeholder="Street Address" 
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
                        <option value="NG">Nigeria (₦)</option>
                        <option value="GH">Ghana (₵)</option>
                        <option value="ZA">South Africa (R)</option>
                        <option value="KE">Kenya (KSh)</option>
                        <option value="US">United States ($)</option>
                        <option value="GB">United Kingdom (£)</option>
                        <option value="CA">Canada ($)</option>
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
                      Continue to Payment Method →
                    </button>
                  </div>
                ) : (
                  <div className={styles.formSection}>
                    <h2 className={styles.sectionTitle}>2. Select Payment Gateway</h2>
                    
                    <div className={styles.paymentMethods}>
                      {/* PAYSTACK METHOD */}
                      <label 
                        className={`${styles.paymentMethod} ${paymentMethod === "paystack" ? styles.activePaymentMethod : ""}`}
                        onClick={() => setPaymentMethod("paystack")}
                      >
                        <input 
                          type="radio" 
                          name="payment" 
                          checked={paymentMethod === "paystack"} 
                          onChange={() => setPaymentMethod("paystack")} 
                        />
                        <div className={styles.methodLabel}>
                          <span>💳 Paystack (Cards, Bank Transfer, USSD, MoMo)</span>
                          <span className={`${styles.badge} ${styles.badgePaystack}`}>INSTANT</span>
                        </div>
                      </label>

                      {/* CRYPTO METHOD */}
                      <label 
                        className={`${styles.paymentMethod} ${paymentMethod === "crypto" ? styles.activePaymentMethod : ""}`}
                        onClick={() => setPaymentMethod("crypto")}
                      >
                        <input 
                          type="radio" 
                          name="payment" 
                          checked={paymentMethod === "crypto"} 
                          onChange={() => setPaymentMethod("crypto")} 
                        />
                        <div className={styles.methodLabel}>
                          <span>🪙 Web3 & Crypto (USDT / SOL / ETH)</span>
                          <span className={`${styles.badge} ${styles.badgeCrypto}`}>ZERO FEE</span>
                        </div>
                      </label>

                      {/* STANDARD CARD METHOD */}
                      <label 
                        className={`${styles.paymentMethod} ${paymentMethod === "card" ? styles.activePaymentMethod : ""}`}
                        onClick={() => setPaymentMethod("card")}
                      >
                        <input 
                          type="radio" 
                          name="payment" 
                          checked={paymentMethod === "card"} 
                          onChange={() => setPaymentMethod("card")} 
                        />
                        <div className={styles.methodLabel}>
                          <span>🌐 Credit / Debit Card (Global)</span>
                        </div>
                      </label>
                    </div>

                    {/* PAYSTACK CURRENCY SELECTOR */}
                    {paymentMethod === "paystack" && (
                      <div className={styles.paystackBox}>
                        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                          Select Local Currency for Paystack Gateway:
                        </p>
                        <div className={styles.currencySelector}>
                          {["NGN", "GHS", "ZAR", "KES", "USD"].map((curr) => (
                            <button
                              key={curr}
                              className={`${styles.currBtn} ${selectedCurrency === curr ? styles.activeCurrBtn : ""}`}
                              onClick={() => setSelectedCurrency(curr)}
                            >
                              {curr}
                            </button>
                          ))}
                        </div>
                        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "1rem" }}>
                          Pay <strong>{selectedCurrency} {(totalUsd * (EXCHANGE_RATES[selectedCurrency] || 1)).toLocaleString()}</strong> via Cards, Instant Virtual Bank Transfer, USSD code, or Mobile Money.
                        </p>
                      </div>
                    )}

                    {/* CRYPTO DEPOSIT INTERFACE */}
                    {paymentMethod === "crypto" && (
                      <div className={styles.cryptoBox}>
                        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>
                          Select Deposit Network:
                        </p>
                        <div className={styles.networkSelector}>
                          {Object.keys(CRYPTO_WALLETS).map((netKey) => (
                            <button
                              key={netKey}
                              className={`${styles.networkBtn} ${selectedCryptoNetwork === netKey ? styles.activeNetworkBtn : ""}`}
                              onClick={() => setSelectedCryptoNetwork(netKey)}
                            >
                              {CRYPTO_WALLETS[netKey].network}
                            </button>
                          ))}
                        </div>

                        <div className={styles.qrContainer}>
                          <img 
                            src={CRYPTO_WALLETS[selectedCryptoNetwork].qr} 
                            alt="Crypto QR Code" 
                            className={styles.qrImg} 
                          />
                          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                            Send exactly <strong>${totalUsd.toFixed(2)} {CRYPTO_WALLETS[selectedCryptoNetwork].symbol}</strong>
                          </p>
                        </div>

                        <div className={styles.walletAddressBox}>
                          <span className={styles.walletAddress}>
                            {CRYPTO_WALLETS[selectedCryptoNetwork].address}
                          </span>
                          <button 
                            className={styles.copyBtn}
                            onClick={() => handleCopyAddress(CRYPTO_WALLETS[selectedCryptoNetwork].address)}
                          >
                            {copied ? "✓ Copied" : "Copy"}
                          </button>
                        </div>

                        <div style={{ marginTop: "1.25rem" }}>
                          <input 
                            type="text" 
                            placeholder="Enter Transaction TxID / Hash after sending" 
                            className={styles.input} 
                            value={txHash}
                            onChange={(e) => setTxHash(e.target.value)}
                          />
                        </div>
                      </div>
                    )}

                    {/* CARD DETAILS */}
                    {paymentMethod === "card" && (
                      <div>
                        <div className={styles.inputGroup}>
                          <input type="text" placeholder="Card Number" className={styles.input} />
                        </div>
                        <div className={styles.inputRow}>
                          <input type="text" placeholder="MM/YY" className={styles.input} />
                          <input type="text" placeholder="CVC" className={styles.input} />
                        </div>
                      </div>
                    )}

                    <div className={styles.actionRow}>
                      <button className="btn btn-ghost" onClick={() => setStep(1)}>
                        ← Back to Shipping
                      </button>
                      <button 
                        className="btn btn-primary" 
                        onClick={handleCompleteOrder}
                        disabled={isProcessing}
                      >
                        {isProcessing ? "Processing..." : `Pay $${totalUsd.toFixed(2)} USD`}
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
                  <div key={item.cartKey || item.id} className={styles.summaryItem}>
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
                  <span>Total (USD)</span>
                  <span>${totalUsd.toFixed(2)}</span>
                </div>
                {paymentMethod === "paystack" && (
                  <div className={styles.totalRow} style={{ color: "#0eba7a", fontSize: "0.9rem", fontWeight: "500" }}>
                    <span>Local ({selectedCurrency})</span>
                    <span>{selectedCurrency} {totalLocal.toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </main>
      <Footer />
      <CartSidebar 
        isOpen={cartOpen} 
        onClose={() => setCartOpen(false)} 
        items={cartItems} 
        onUpdateQty={updateQty} 
        onRemove={removeFromCart} 
      />
    </>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<div>Loading checkout...</div>}>
      <CheckoutContent />
    </Suspense>
  );
}
