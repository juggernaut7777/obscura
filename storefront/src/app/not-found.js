"use client";
import Link from "next/link";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

export default function NotFound() {
  return (
    <>
      <Header cartCount={0} onCartClick={() => {}} />
      <main style={{
        minHeight: "80vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "2rem"
      }}>
        <h1 className="heading-display" style={{ fontSize: "6rem", marginBottom: "1rem" }}>404</h1>
        <h2 style={{ marginBottom: "2rem", color: "var(--text-secondary)", fontWeight: 400 }}>Piece Not Found</h2>
        <p style={{ maxWidth: "400px", marginBottom: "3rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
          The garment you are looking for has been archived, sold out, or never existed.
        </p>
        <Link href="/shop" className="btn btn-primary">
          Return to Collection
        </Link>
      </main>
      <Footer />
    </>
  );
}
