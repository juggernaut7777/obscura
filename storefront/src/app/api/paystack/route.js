import { NextResponse } from "next/server";

const PAYSTACK_SECRET_KEY = process.env.PAYSTACK_SECRET_KEY || "sk_test_mock_paystack_key_obscura_2026";

// Exchange rates (relative to USD 1.00)
const EXCHANGE_RATES = {
  USD: 1.0,
  NGN: 1500.0,
  GHS: 15.5,
  ZAR: 18.5,
  KES: 130.0
};

export async function POST(request) {
  try {
    const body = await request.json();
    const { action, email, amount_usd, currency = "NGN", callback_url, reference } = body;

    // 1. VERIFY TRANSACTION ACTION
    if (action === "verify") {
      if (!reference) {
        return NextResponse.json({ success: false, error: "Missing reference" }, { status: 400 });
      }

      // If running with mock test key, simulate success
      if (PAYSTACK_SECRET_KEY.includes("mock")) {
        return NextResponse.json({
          success: true,
          status: "success",
          reference,
          gateway_response: "Successful (Mock)",
          paid_at: new Date().toISOString()
        });
      }

      const verifyRes = await fetch(`https://api.paystack.co/transaction/verify/${reference}`, {
        headers: {
          Authorization: `Bearer ${PAYSTACK_SECRET_KEY}`
        }
      });
      const verifyData = await verifyRes.json();

      if (verifyData.status && verifyData.data.status === "success") {
        return NextResponse.json({
          success: true,
          status: "success",
          reference,
          amount: verifyData.data.amount / 100,
          currency: verifyData.data.currency,
          paid_at: verifyData.data.paid_at
        });
      } else {
        return NextResponse.json({
          success: false,
          error: verifyData.message || "Payment verification failed"
        }, { status: 400 });
      }
    }

    // 2. INITIALIZE TRANSACTION ACTION
    const rate = EXCHANGE_RATES[currency] || 1500.0;
    const localAmount = amount_usd * rate;
    const amountInKobo = Math.round(localAmount * 100);

    const paystackRef = `OBS-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    if (PAYSTACK_SECRET_KEY.includes("mock")) {
      return NextResponse.json({
        success: true,
        reference: paystackRef,
        authorization_url: `https://checkout.paystack.com/mock-pay-${paystackRef}`,
        currency,
        amount_local: localAmount,
        amount_usd,
        is_mock: true
      });
    }

    const initRes = await fetch("https://api.paystack.co/transaction/initialize", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${PAYSTACK_SECRET_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email,
        amount: amountInKobo,
        currency,
        reference: paystackRef,
        callback_url: callback_url || "http://localhost:3000/checkout?paystack_verify=true",
        channels: ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"]
      })
    });

    const initData = await initRes.json();

    if (initData.status) {
      return NextResponse.json({
        success: true,
        authorization_url: initData.data.authorization_url,
        access_code: initData.data.access_code,
        reference: initData.data.reference,
        currency,
        amount_local: localAmount
      });
    } else {
      return NextResponse.json({
        success: false,
        error: initData.message || "Paystack initialization failed"
      }, { status: 500 });
    }

  } catch (error) {
    console.error("[PAYSTACK API] Error:", error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
