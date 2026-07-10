import pytest
from pricing_engine import calculate_final_price

def test_calculate_final_price_usd_invalid_inputs():
    """Test that invalid inputs return a dictionary with zeroes."""
    expected = {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}

    assert calculate_final_price(0, "USD") == expected
    assert calculate_final_price(-10, "USD") == expected
    assert calculate_final_price("invalid", "USD") == expected
    assert calculate_final_price(None, "USD") == expected

def test_calculate_final_price_usd_string_input():
    """Test that a valid string float is correctly parsed and calculated."""
    # 10 < 20, margin_mult = 1.6
    res = calculate_final_price("10", "USD")
    assert res["base_usd"] == 10.0
    assert res["margin_tier"] == 1.6
    assert res["final_usd"] == 18.99
    assert res["profit_usd"] == 6.14

def test_calculate_final_price_usd_tier_1_6():
    """Test pricing for USD item under $20 (1.6x multiplier)."""
    # 10 < 20, margin_mult = 1.6
    res = calculate_final_price(10, "USD")
    assert res["base_usd"] == 10.0
    assert res["margin_tier"] == 1.6
    assert res["final_usd"] == 18.99
    assert res["profit_usd"] == 6.14

def test_calculate_final_price_usd_tier_1_4():
    """Test pricing for USD item under $50 (1.4x multiplier)."""
    # 30 < 50, margin_mult = 1.4
    res = calculate_final_price(30, "USD")
    assert res["base_usd"] == 30.0
    assert res["margin_tier"] == 1.4

    # retail_before_stripe = (30 * 1.4) + 2.0 = 42 + 2 = 44
    # final_price = math.ceil((44 + 0.30) / 0.971) - 0.01 = math.ceil(45.623) - 0.01 = 45.99
    # stripe_total = (45.99 * 0.029) + 0.30 = 1.33371 + 0.30 = 1.63371
    # profit = 45.99 - 30 - 1.63371 - 2.0 = 12.35629 -> 12.36
    assert res["final_usd"] == 45.99
    assert res["profit_usd"] == 12.36

def test_calculate_final_price_usd_tier_1_3():
    """Test pricing for USD item under $100 (1.3x multiplier)."""
    # 60 < 100, margin_mult = 1.3
    res = calculate_final_price(60, "USD")
    assert res["base_usd"] == 60.0
    assert res["margin_tier"] == 1.3

    # retail_before_stripe = (60 * 1.3) + 2.0 = 78 + 2 = 80
    # final_price = math.ceil((80 + 0.30) / 0.971) - 0.01 = math.ceil(82.698) - 0.01 = 82.99
    # stripe_total = (82.99 * 0.029) + 0.30 = 2.40671 + 0.30 = 2.70671
    # profit = 82.99 - 60 - 2.70671 - 2.0 = 18.28329 -> 18.28
    assert res["final_usd"] == 82.99
    assert res["profit_usd"] == 18.28

def test_calculate_final_price_usd_tier_1_25():
    """Test pricing for USD item $100 or over (1.25x multiplier)."""
    # 120 >= 100, margin_mult = 1.25
    res = calculate_final_price(120, "USD")
    assert res["base_usd"] == 120.0
    assert res["margin_tier"] == 1.25

    # retail_before_stripe = (120 * 1.25) + 2.0 = 150 + 2 = 152
    # final_price = math.ceil((152 + 0.30) / 0.971) - 0.01 = math.ceil(156.848) - 0.01 = 156.99
    # stripe_total = (156.99 * 0.029) + 0.30 = 4.55271 + 0.30 = 4.85271
    # profit = 156.99 - 120 - 4.85271 - 2.0 = 30.13729 -> 30.14
    assert res["final_usd"] == 156.99
    assert res["profit_usd"] == 30.14
