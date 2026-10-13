import { Inter } from "next/font/google";
import "./globals.css";
import { CartProvider } from "@/context/CartContext";
import { WishlistProvider } from "@/context/WishlistContext";
import { CurrencyProvider } from "@/context/CurrencyContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "OBSCURA — ARCHITECTURAL HAUTE STREETWEAR // VOGUE EDITORIAL ARCHIVE",
  description: "High-end brutalist fashion and custom-milled heavyweight streetwear. 480–520 GSM loopback cotton, geometric tailoring, and DDP worldwide expedited delivery.",
  keywords: "haute couture, high fashion, streetwear, architectural clothing, 500 gsm hoodie, brutalist fashion, vogue editorial, balenciaga aesthetic",
  openGraph: {
    title: "OBSCURA — ARCHITECTURAL HAUTE STREETWEAR",
    description: "High-end brutalist fashion and custom-milled heavyweight streetwear. Milled fabrics, raw silhouettes, zero commercial shortcuts.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <CurrencyProvider>
          <CartProvider>
            <WishlistProvider>
              {children}
            </WishlistProvider>
          </CartProvider>
        </CurrencyProvider>
      </body>
    </html>
  );
}
