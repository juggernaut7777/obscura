"use client";
import { useState } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { useCart } from "@/context/CartContext";
import styles from "./page.module.css";

const FAQ_DATA = [
  {
    category: "Ordering",
    questions: [
      {
        q: "How do I place an order?",
        a: "Browse our collection, select your size and color, then add to cart. Follow the checkout flow to complete your purchase. You'll receive an order confirmation email within minutes."
      },
      {
        q: "Can I modify or cancel my order?",
        a: "Orders can be modified or cancelled within 2 hours of placement. After that, your order enters our fulfillment pipeline. Contact us at support@obscura.co for urgent changes."
      },
      {
        q: "Are your products authentic?",
        a: "Every piece in our collection is sourced directly from independent Asian ateliers and premium blank manufacturers. We curate original designs and heavyweight basics — no mass-market fast fashion."
      }
    ]
  },
  {
    category: "Shipping & Delivery",
    questions: [
      {
        q: "How long does shipping take?",
        a: "Standard shipping takes 10–18 business days. All orders ship directly from our curated warehouse partners via air freight. You'll receive tracking within 3–5 business days of placing your order."
      },
      {
        q: "Do you offer free shipping?",
        a: "Yes — free shipping on all orders over $200. Standard flat rate of $15 applies to orders under $200."
      },
      {
        q: "Do you ship internationally?",
        a: "We ship worldwide. International orders may be subject to customs duties and import taxes, which are the responsibility of the buyer. Delivery times vary by destination."
      }
    ]
  },
  {
    category: "Returns & Exchanges",
    questions: [
      {
        q: "What is your return policy?",
        a: "We accept returns within 14 days of delivery for unworn, unwashed items with tags attached. Items must be in original condition. Contact support@obscura.co to initiate a return."
      },
      {
        q: "How do exchanges work?",
        a: "For exchanges, initiate a return and place a new order for your preferred size or color. This ensures the fastest turnaround while stock is available."
      },
      {
        q: "Who pays for return shipping?",
        a: "Return shipping costs are the responsibility of the buyer unless the item is defective or we made an error. We'll provide a prepaid label for defective items."
      }
    ]
  },
  {
    category: "Sizing",
    questions: [
      {
        q: "How do your pieces fit?",
        a: "Our pieces generally run true to size with a relaxed, slightly oversized silhouette — typical of premium streetwear. Check individual product pages for specific size charts and fit notes."
      },
      {
        q: "What if my size is out of stock?",
        a: "We restock popular pieces regularly. Join our newsletter or follow us on Instagram for restock notifications. Some limited drops do not restock once sold out."
      },
      {
        q: "Do you have a size chart?",
        a: "Yes — each product page includes detailed measurements. We list chest width, body length, and sleeve length in both cm and inches. When in doubt, size up for a comfortable layered fit."
      }
    ]
  },
  {
    category: "Payment",
    questions: [
      {
        q: "What payment methods do you accept?",
        a: "We accept Visa, Mastercard, Apple Pay, and select local payment methods depending on your region. All transactions are secured with industry-standard encryption."
      },
      {
        q: "Is my payment information secure?",
        a: "Absolutely. We use PCI-compliant payment processing and never store your card details on our servers. Your financial data is encrypted end-to-end."
      },
      {
        q: "Do you offer payment plans?",
        a: "We're working on integrating buy-now-pay-later options. Stay tuned for updates via our newsletter."
      }
    ]
  }
];

function AccordionItem({ question, answer }) {
  const [open, setOpen] = useState(false);

  return (
    <div className={`${styles.item} ${open ? styles.itemOpen : ""}`}>
      <button className={styles.question} onClick={() => setOpen(!open)}>
        <span>{question}</span>
        <svg
          className={`${styles.chevron} ${open ? styles.chevronOpen : ""}`}
          width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
        >
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </button>
      <div className={`${styles.answer} ${open ? styles.answerOpen : ""}`}>
        <p>{answer}</p>
      </div>
    </div>
  );
}

export default function FAQPage() {
  const { cartItems, setCartOpen } = useCart();

  return (
    <>
      <Header cartCount={cartItems.length} onCartClick={() => setCartOpen(true)} />
      <main className={styles.main}>
        <div className={styles.hero}>
          <span className={styles.label}>Support</span>
          <h1 className={styles.title}>Frequently Asked Questions</h1>
          <p className={styles.subtitle}>
            Everything you need to know about shopping with OBSCURA.
          </p>
        </div>

        <div className={styles.content}>
          {FAQ_DATA.map((section) => (
            <div key={section.category} className={styles.section}>
              <h2 className={styles.categoryTitle}>{section.category}</h2>
              <div className={styles.questions}>
                {section.questions.map((item) => (
                  <AccordionItem key={item.q} question={item.q} answer={item.a} />
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className={styles.contact}>
          <h3>Still have questions?</h3>
          <p>Reach out to our team at <a href="mailto:support@obscura.co">support@obscura.co</a></p>
        </div>
      </main>
      <Footer />
    </>
  );
}
