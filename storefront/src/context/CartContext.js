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

  const addToCart = (product, arg2 = 1, arg3, arg4) => {
    let quantity = 1;
    let selectedColor = product.selectedColor || null;
    let selectedSize = product.selectedSize || null;

    if (typeof arg2 === "string") {
      // Called as addToCart(product, color, size, quantity)
      selectedColor = arg2;
      selectedSize = typeof arg3 === "string" ? arg3 : selectedSize;
      quantity = typeof arg4 === "number" ? arg4 : 1;
    } else if (typeof arg2 === "number") {
      // Called as addToCart(product, quantity)
      quantity = arg2;
    }

    setCartItems((prev) => {
      const cartKey = [product.id, selectedColor, selectedSize]
        .filter(Boolean)
        .join("-");
      const existing = prev.find((item) => item.cartKey === cartKey);
      if (existing) {
        return prev.map((item) =>
          item.cartKey === cartKey ? { ...item, qty: Number(item.qty || 1) + Number(quantity) } : item
        );
      }
      return [
        ...prev,
        {
          ...product,
          selectedColor,
          selectedSize,
          color: selectedColor || product.color,
          size: selectedSize || product.size,
          cartKey,
          qty: Number(quantity)
        }
      ];
    });
    setCartOpen(true);
  };

  const updateQty = (key, newQty) => {
    if (newQty < 1) return removeItem(key);
    setCartItems((prev) =>
      prev.map((item) => (item.cartKey === key || item.id === key ? { ...item, qty: newQty } : item))
    );
  };

  const removeItem = (key) => {
    setCartItems((prev) => prev.filter((item) => item.cartKey !== key && item.id !== key));
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
        removeFromCart: removeItem, // Alias for checkout compatibility
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
