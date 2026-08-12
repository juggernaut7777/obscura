import pytest
from pricing_engine import calculate_final_price

def test_invalid_and_zero_inputs():
    # Invalid string
    res = calculate_final_price("invalid")
    assert res == {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}

    # Zero or negative
    res = calculate_final_price(0)
    assert res == {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}

    res = calculate_final_price(-10)
    assert res == {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}

def test_usd_pricing_tiers():
    # Base < 20 (margin_mult = 1.6)
    res = calculate_final_price(10, "USD")
    assert res["base_usd"] == 10.0
    assert res["margin_tier"] == 1.6

    # Base < 50 (margin_mult = 1.4)
    res = calculate_final_price(30, "USD")
    assert res["margin_tier"] == 1.4

    # Base < 100 (margin_mult = 1.3)
    res = calculate_final_price(75, "USD")
    assert res["margin_tier"] == 1.3

    # Base >= 100 (margin_mult = 1.25)
    res = calculate_final_price(150, "USD")
    assert res["margin_tier"] == 1.25

def test_cny_pricing_tiers():
    # Note: threshold is evaluated against CNY value directly
    # Val < 100 (margin_mult = 2.2)
    res = calculate_final_price(50, "CNY")
    assert res["margin_tier"] == 2.2

    # Val < 300 (margin_mult = 1.8)
    res = calculate_final_price(150, "CNY")
    assert res["margin_tier"] == 1.8

    # Val < 600 (margin_mult = 1.6)
    res = calculate_final_price(450, "CNY")
    assert res["margin_tier"] == 1.6

    # Val >= 600 (margin_mult = 1.4)
    res = calculate_final_price(1200, "CNY")
    assert res["margin_tier"] == 1.4

def test_case_insensitivity():
    res_lower = calculate_final_price(10, "usd")
    res_upper = calculate_final_price(10, "USD")
    assert res_lower == res_upper
