import pytest
from goal2_sourcing_engine.pricing_engine import calculate_final_price

def test_calculate_final_price_error_cases():
    """Test that invalid, zero, or negative prices return the default zero-value dictionary."""
    expected = {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}

    assert calculate_final_price(0) == expected
    assert calculate_final_price(-10) == expected
    assert calculate_final_price("invalid") == expected
    assert calculate_final_price(None) == expected

def test_calculate_final_price_usd_tiers():
    """Test the tiered margin strategy for USD source currency."""
    # Tier 1: base_usd < 20 (e.g. 10)
    res = calculate_final_price(10, currency="USD")
    assert res["margin_tier"] == 1.6
    assert "final_usd" in res
    assert "profit_usd" in res
    assert res["base_usd"] == 10.0

    # Tier 2: base_usd < 50 (e.g. 30)
    res = calculate_final_price(30, currency="USD")
    assert res["margin_tier"] == 1.4

    # Tier 3: base_usd < 100 (e.g. 60)
    res = calculate_final_price(60, currency="USD")
    assert res["margin_tier"] == 1.3

    # Tier 4: base_usd >= 100 (e.g. 120)
    res = calculate_final_price(120, currency="USD")
    assert res["margin_tier"] == 1.25

def test_calculate_final_price_cny_tiers():
    """Test the tiered margin strategy for CNY source currency (default)."""
    # Tier 1: val < 100 (e.g. 50)
    res = calculate_final_price(50, currency="CNY")
    assert res["margin_tier"] == 2.2
    assert "final_usd" in res
    assert "profit_usd" in res
    assert res["base_usd"] == round(50 / 7.2, 2)

    # Tier 2: val < 300 (e.g. 150)
    res = calculate_final_price(150, currency="CNY")
    assert res["margin_tier"] == 1.8

    # Tier 3: val < 600 (e.g. 450)
    res = calculate_final_price(450, currency="CNY")
    assert res["margin_tier"] == 1.6

    # Tier 4: val >= 600 (e.g. 1200)
    res = calculate_final_price(1200, currency="CNY")
    assert res["margin_tier"] == 1.4

    # Verify default currency is CNY
    res_default = calculate_final_price(50)
    assert res_default["margin_tier"] == 2.2
