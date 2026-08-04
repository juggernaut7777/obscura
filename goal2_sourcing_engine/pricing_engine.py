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
import functools

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

class PricingEngine:
    def __init__(self):
        pass

    def calculate_final_price(self, price, currency="CNY"):
        return calculate_final_price(price, currency)

    # ⚡ Bolt: Performance optimization
    # Why: Speed up repeated pricing calculations across many items.
    # What: Add LRU caching to the pricing calculations.
    @functools.lru_cache(maxsize=1024)
    def calculate_physical_retail_price(self, supplier_cost, category="apparel"):
        # Use USD flow since supplier_cost is in USD
        res = calculate_final_price(supplier_cost, "USD")
        
        # Floor: never sell below $29 (accessories/hats), T-shirts are $31 minimum, Jackets are exactly $89
        cat_lower = str(category).lower()
        sell_price = res["final_usd"]
        
        if "jacket" in cat_lower or "coat" in cat_lower or "outerwear" in cat_lower:
            sell_price = max(sell_price, 89.0)
        elif "t-shirt" in cat_lower or "tee" in cat_lower or "top" in cat_lower:
            sell_price = max(sell_price, 31.0)
        else:
            sell_price = max(sell_price, 29.0)
            
        # Recompute net profit for adjusted price
        stripe_total = (sell_price * STRIPE_FEE_PERCENT) + STRIPE_FEE_FIXED
        net_profit = sell_price - supplier_cost - stripe_total - BUFFER_FEE

        return {
            "retail_price": round(sell_price, 2),
            "net_profit": round(net_profit, 2)
        }


if __name__ == "__main__":
    # Test cases
    test_cny_prices = [50, 150, 450, 1200]
    print("=== CNY TEST CASES ===")
    print(f"{'CNY':<8} | {'Final USD':<12} | {'Profit':<10} | {'Tier'}")
    print("-" * 50)
    for p in test_cny_prices:
        res = calculate_final_price(p, "CNY")
        print(f"¥{p:<7} | ${res['final_usd']:<11} | ${res['profit_usd']:<9} | {res['margin_tier']}x")
        
    test_usd_prices = [10, 25, 60, 150]
    print("\n=== USD TEST CASES ===")
    print(f"{'USD':<8} | {'Final USD':<12} | {'Profit':<10} | {'Tier'}")
    print("-" * 50)
    for p in test_usd_prices:
        res = calculate_final_price(p, "USD")
        print(f"${p:<7} | ${res['final_usd']:<11} | ${res['profit_usd']:<9} | {res['margin_tier']}x")
