import { NextResponse } from "next/server";

// Storefront Crypto Treasury Deposit Addresses
const CRYPTO_WALLETS = {
  USDT_TRC20: {
    network: "TRON (TRC20)",
    symbol: "USDT",
    address: "TX9Kz8g5R4P2mN7vQ1wL9yE3H6jF0bC4aS",
    qr_code_url: "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=TX9Kz8g5R4P2mN7vQ1wL9yE3H6jF0bC4aS"
  },
  USDT_BEP20: {
    network: "BNB Smart Chain (BEP20)",
    symbol: "USDT",
    address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
    qr_code_url: "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
  },
  SOL: {
    network: "Solana (SOL)",
    symbol: "SOL",
    address: "7xKXtg2CW87d97TXwSDPjN5w4P5sB4sE2q1v3W9yZ8mK",
    qr_code_url: "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=7xKXtg2CW87d97TXwSDPjN5w4P5sB4sE2q1v3W9yZ8mK"
  },
  ETH: {
    network: "Ethereum (ERC20)",
    symbol: "ETH / USDC",
    address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
    qr_code_url: "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
  }
};

export async function GET() {
  return NextResponse.json({
    success: true,
    wallets: CRYPTO_WALLETS
  });
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { action, tx_hash, network = "USDT_TRC20", amount_usd } = body;

    if (action === "verify_tx") {
      if (!tx_hash) {
        return NextResponse.json({ success: false, error: "Missing transaction hash / TxID" }, { status: 400 });
      }

      // Mock verification for web demo (instantly approves clean TxIDs)
      const isValid = tx_hash.length >= 10;
      return NextResponse.json({
        success: isValid,
        status: isValid ? "confirmed" : "pending",
        tx_hash,
        network,
        amount_usd,
        confirmations: isValid ? 12 : 0,
        confirmed_at: new Date().toISOString()
      });
    }

    const walletInfo = CRYPTO_WALLETS[network] || CRYPTO_WALLETS.USDT_TRC20;
    const paymentRef = `CRYPTO-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    return NextResponse.json({
      success: true,
      reference: paymentRef,
      network: walletInfo.network,
      symbol: walletInfo.symbol,
      address: walletInfo.address,
      qr_code_url: walletInfo.qr_code_url,
      amount_usd
    });

  } catch (error) {
    console.error("[CRYPTO API] Error:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
