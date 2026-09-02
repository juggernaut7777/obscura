import { Inter } from "next/font/google";
import "./globals.css";
import { CartProvider } from "@/context/CartContext";
import { WishlistProvider } from "@/context/WishlistContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "OBSCURA — Curated Fashion",
  description: "Premium aesthetically curated fashion. Discover handpicked pieces that define your personal style. Modern silhouettes, timeless quality.",
  keywords: "fashion, streetwear, aesthetic clothing, curated fashion, premium apparel, Y2K, vintage, modern fashion",
  openGraph: {
    title: "OBSCURA — Curated Fashion",
    description: "Premium aesthetically curated fashion. Discover handpicked pieces that define your personal style.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CartProvider>
          <WishlistProvider>
            {children}
          </WishlistProvider>
        </CartProvider>
      </body>
    </html>
  );
}
