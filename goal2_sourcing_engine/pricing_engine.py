"""
PRICING ENGINE — Currency, Fees, and Profit Optimization
========================================================
Converts CNY (Yuan) to USD, adds platform fees, DDP agent fees,
and applies a tiered profit margin strategy.

DDP Model (Africa): 
  - DDP agent handling: $3/item (purchasing + QC + consolidation)
  - Crypto payment to agent: ~$1.50 USDT network fee
  - DDP shipping to Africa: ~$12/kg (included in customer shipping charge)
  - Buffer for customs/fluctuations: $2.00

Strategy: "Higher price = Higher absolute gain"
"""

import math

# CONFIGURATION
CNY_TO_USD_RATE = 7.2       # current market rate
STRIPE_FEE_PERCENT = 0.029  # 2.9%
STRIPE_FEE_FIXED = 0.30     # $0.30
DDP_HANDLING_FEE = 3.00     # $3.00 per item (DDP agent purchasing + QC + consolidation)
CRYPTO_FEE = 1.50           # $1.50 estimated USDT fee for agent payment
BUFFER_FEE = 2.00           # $2.00 for customs variance / exchange rate drift / misc

def calculate_final_price(price, currency="CNY"):
    """
    Calculates the final retail price in USD.
    Higher original price = Higher dollar gain.
    Supports CNY and USD source currencies.
    """
    try:
        val = float(price)
        if val <= 0:
            return {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}
    except:
        return {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}

    # 1. Base Cost in USD
    if currency.upper() == "USD":
        base_usd = val
        operational_fees = BUFFER_FEE  # No international sourcing fees for USD Shopify products
        
        # Tiered Margin Strategy for USD-sourced items (e.g. markup by 1.25x to 1.6x)
        if base_usd < 20:
            margin_mult = 1.6
        elif base_usd < 50:
            margin_mult = 1.4
        elif base_usd < 100:
            margin_mult = 1.3
        else:
            margin_mult = 1.25
            
        retail_before_stripe = (base_usd * margin_mult) + operational_fees
        final_price = (retail_before_stripe + STRIPE_FEE_FIXED) / (1 - STRIPE_FEE_PERCENT)
        final_price = math.ceil(final_price) - 0.01
        
        stripe_total = (final_price * STRIPE_FEE_PERCENT) + STRIPE_FEE_FIXED
        profit = final_price - base_usd - stripe_total - BUFFER_FEE
        
        return {
            "final_usd": round(final_price, 2),
            "base_usd": round(base_usd, 2),
            "profit_usd": round(profit, 2),
            "margin_tier": margin_mult
        }
    else:
        # CNY flow — DDP agent sourcing from Chinese marketplaces
        base_usd = val / CNY_TO_USD_RATE
        operational_fees = DDP_HANDLING_FEE + CRYPTO_FEE + BUFFER_FEE

        # Tiered Margin Strategy — higher margins on cheaper items
        # (DDP shipping cost to Africa is charged separately to customer)
        if val < 100:
            margin_mult = 2.2
        elif val < 300:
            margin_mult = 1.8
        elif val < 600:
            margin_mult = 1.6
        else:
            margin_mult = 1.4

        retail_before_stripe = (base_usd * margin_mult) + operational_fees
        final_price = (retail_before_stripe + STRIPE_FEE_FIXED) / (1 - STRIPE_FEE_PERCENT)
        final_price = math.ceil(final_price) - 0.01

        stripe_total = (final_price * STRIPE_FEE_PERCENT) + STRIPE_FEE_FIXED
        profit = final_price - base_usd - stripe_total - DDP_HANDLING_FEE - CRYPTO_FEE - BUFFER_FEE

        return {
            "final_usd": round(final_price, 2),
            "base_usd": round(base_usd, 2),
            "profit_usd": round(profit, 2),
            "margin_tier": margin_mult
        }

DDP_SHIPPING_PER_KG_USD = 12.00  # $12.00 per kg DDP Air Express freight


def calculate_shipping_cost(weight_grams: float = 500.0, is_set: bool = False, piece_weights: list = None) -> dict:
    """
    Calculates exact DDP air freight shipping cost based on weight in grams.
    For sets with multiple weight photos (e.g. top + pants + accessory),
    automatically merges and sums the weights together.
    """
    if piece_weights and len(piece_weights) > 0:
        total_weight = sum([float(w) for w in piece_weights if w and float(w) > 0])
    else:
        total_weight = float(weight_grams or 500.0)
        
    kg = max(0.2, total_weight / 1000.0)
    shipping_cost_usd = round(kg * DDP_SHIPPING_PER_KG_USD, 2)
    
    return {
        "total_weight_grams": round(total_weight, 1),
        "total_weight_kg": round(kg, 3),
        "shipping_cost_usd": shipping_cost_usd,
        "is_set": is_set or bool(piece_weights and len(piece_weights) > 1),
        "piece_count": len(piece_weights) if piece_weights else 1
    }


class PricingEngine:
    def __init__(self):
        pass

    def calculate_final_price(self, price, currency="CNY"):
        return calculate_final_price(price, currency)

    def calculate_shipping(self, weight_grams: float = 500.0, piece_weights: list = None) -> dict:
        return calculate_shipping_cost(weight_grams=weight_grams, piece_weights=piece_weights)

    def calculate_physical_retail_price(self, supplier_cost, category="apparel", weight_grams: float = 500.0):
        # Use USD flow since supplier_cost is in USD
        res = calculate_final_price(supplier_cost, "USD")
        shipping = calculate_shipping_cost(weight_grams)
        
        # Floor: never sell below $29 (accessories/hats), T-shirts are $31 minimum, Sets/Jackets are $89 minimum
        cat_lower = str(category).lower()
        sell_price = res["final_usd"]
        
        if "set" in cat_lower or "tracksuit" in cat_lower or "jacket" in cat_lower or "coat" in cat_lower:
            sell_price = max(sell_price, 89.0)
        elif "t-shirt" in cat_lower or "tee" in cat_lower or "top" in cat_lower:
            sell_price = max(sell_price, 31.0)
        elif "pants" in cat_lower or "trouser" in cat_lower:
            sell_price = max(sell_price, 59.0)
        else:
            sell_price = max(sell_price, 29.0)
            
        # Recompute net profit including shipping buffer
        stripe_total = (sell_price * STRIPE_FEE_PERCENT) + STRIPE_FEE_FIXED
        net_profit = sell_price - supplier_cost - stripe_total - BUFFER_FEE

        return {
            "retail_price": round(sell_price, 2),
            "net_profit": round(net_profit, 2),
            "shipping_details": shipping
        }


if __name__ == "__main__":
    # Test cases
    print("=== MULTI-PIECE SET WEIGHT & SHIPPING TEST ===")
    set_test = calculate_shipping_cost(piece_weights=[580, 520, 100]) # top (580g) + pants (520g) + packaging (100g)
    print(f"2-Piece Tracksuit Set: {set_test['total_weight_grams']}g ({set_test['total_weight_kg']} kg) -> Shipping: ${set_test['shipping_cost_usd']}")

    test_cny_prices = [50, 150, 450, 1200]
    print("\n=== CNY TEST CASES ===")
    print(f"{'CNY':<8} | {'Final USD':<12} | {'Profit':<10} | {'Tier'}")
    print("-" * 50)
    for p in test_cny_prices:
        res = calculate_final_price(p, "CNY")
        print(f"¥{p:<7} | ${res['final_usd']:<11} | ${res['profit_usd']:<9} | {res['margin_tier']}x")

