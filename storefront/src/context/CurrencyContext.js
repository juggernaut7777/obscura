"use client";
import { createContext, useContext, useState, useEffect } from "react";

const RATES = {
  USD: { symbol: "$", rate: 1.0, label: "USD ($)" },
  EUR: { symbol: "€", rate: 0.92, label: "EUR (€)" },
  GBP: { symbol: "£", rate: 0.79, label: "GBP (£)" },
  JPY: { symbol: "¥", rate: 154.5, label: "JPY (¥)" }
};

const CurrencyContext = createContext();

export function CurrencyProvider({ children }) {
  const [currency, setCurrency] = useState("USD");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("obscura_currency");
      if (saved && RATES[saved]) {
        setCurrency(saved);
      }
    } catch {
      // LocalStorage unavailable
    }
  }, []);

  const changeCurrency = (code) => {
    if (RATES[code]) {
      setCurrency(code);
      try {
        localStorage.setItem("obscura_currency", code);
      } catch {}
    }
  };

  const formatPrice = (amountUsd) => {
    if (amountUsd == null || isNaN(amountUsd)) return "$0.00";
    const info = RATES[currency] || RATES.USD;
    const converted = Number(amountUsd) * info.rate;
    if (currency === "JPY") {
      return `${info.symbol}${Math.round(converted).toLocaleString()}`;
    }
    return `${info.symbol}${converted.toFixed(2)}`;
  };

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency: changeCurrency, formatPrice, currencies: RATES }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (!context) {
    return {
      currency: "USD",
      setCurrency: () => {},
      formatPrice: (amt) => `$${amt?.toFixed(2) || "0.00"}`,
      currencies: RATES
    };
  }
  return context;
}
