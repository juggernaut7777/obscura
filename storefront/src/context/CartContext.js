"use client";
import { createContext, useContext, useState, useEffect } from "react";

const CartContext = createContext();

export function CartProvider({ children }) {
  const [cartItems, setCartItems] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("obscura_cart");
      if (saved) {
        setCartItems(JSON.parse(saved));
      }
    } catch (e) {
      console.error("Error parsing cart data", e);
    }
    setLoaded(true);
  }, []);

  // Save to localStorage when updated
  useEffect(() => {
    if (loaded) {
      try {
        localStorage.setItem("obscura_cart", JSON.stringify(cartItems));
      } catch (e) {
        console.error("Error saving cart data", e);
      }
    }
  }, [cartItems, loaded]);

  const addToCart = (product, quantity = 1) => {
    setCartItems((prev) => {
      // Build unique key from product id + selected color + selected size
      const cartKey = [product.id, product.selectedColor, product.selectedSize]
        .filter(Boolean)
        .join("-");
      const existing = prev.find((item) => item.cartKey === cartKey);
      if (existing) {
        return prev.map((item) =>
          item.cartKey === cartKey ? { ...item, qty: item.qty + quantity } : item
        );
      }
      return [...prev, { ...product, cartKey, qty: quantity }];
    });
    setCartOpen(true);
  };

  const updateQty = (cartKey, newQty) => {
    if (newQty < 1) return removeItem(cartKey);
    setCartItems((prev) =>
      prev.map((item) => (item.cartKey === cartKey ? { ...item, qty: newQty } : item))
    );
  };

  const removeItem = (cartKey) => {
    setCartItems((prev) => prev.filter((item) => item.cartKey !== cartKey));
  };

  const clearCart = () => {
    setCartItems([]);
  };

  return (
    <CartContext.Provider
      value={{
        cartItems,
        cartOpen,
        setCartOpen,
        addToCart,
        updateQty,
        removeItem,
        clearCart,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
