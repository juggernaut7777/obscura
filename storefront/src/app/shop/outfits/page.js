"use client";
import { useCart } from "@/context/CartContext";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import { DEMO_OUTFITS, DEMO_PRODUCTS } from "@/data/products";
import styles from "./page.module.css";

export default function OutfitsPage() {
  const { cartItems, cartOpen, setCartOpen, updateQty, removeItem, addToCart } = useCart();

  const shopTheLook = (outfit) => {
    // Add all products in the outfit to cart
    outfit.products.forEach(productId => {
      const product = DEMO_PRODUCTS.find(p => p.id === productId);
      if (product) {
        addToCart(product, 1);
      }
    });
    setCartOpen(true);
  };

  return (
    <>
      <Header cartCount={cartItems.length} onCartClick={() => setCartOpen(true)} />
      <CartSidebar
        isOpen={cartOpen}
        onClose={() => setCartOpen(false)}
        items={cartItems}
        onUpdateQty={updateQty}
        onRemove={removeItem}
      />

      <main className={styles.main}>
        <header className={styles.header}>
          <div className="container">
            <h1 className={`heading-display ${styles.title}`}>Curated Outfits</h1>
            <p className={styles.subtitle}>
              Full aesthetic ensembles styled by Obscura. Shop the complete look.
            </p>
          </div>
        </header>

        <section className={`container ${styles.outfitsSection}`}>
          <div className={styles.grid}>
            {DEMO_OUTFITS.map((outfit) => (
              <div key={outfit.id} className={styles.outfitCard}>
                <div className={styles.imageContainer}>
                  <img src={outfit.image} alt={outfit.name} className={styles.outfitImage} />
                  <div className={styles.tags}>
                    {outfit.tags.map(tag => <span key={tag} className={styles.tag}>{tag}</span>)}
                  </div>
                </div>
                <div className={styles.info}>
                  <h2 className={styles.outfitName}>{outfit.name}</h2>
                  <p className={styles.outfitDescription}>{outfit.description}</p>
                  <div className={styles.priceContainer}>
                    <span className={styles.price}>${outfit.price}</span>
                    <span className={styles.outfitLabel}>Full Look</span>
                  </div>
                  
                  <div className={styles.productsList}>
                    <p className={styles.includesTitle}>Includes:</p>
                    <ul>
                      {outfit.products.map(pId => {
                        const p = DEMO_PRODUCTS.find(x => x.id === pId);
                        return p ? (
                          <li key={pId}>
                            <Link href={`/product/${pId}`}>{p.name}</Link>
                          </li>
                        ) : null;
                      })}
                    </ul>
                  </div>

                  <button 
                    className="btn btn-primary" 
                    onClick={() => shopTheLook(outfit)}
                    style={{ width: '100%', marginTop: '1rem' }}
                  >
                    Shop The Look
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
