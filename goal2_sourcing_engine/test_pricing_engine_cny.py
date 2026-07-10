import pytest
from pricing_engine import calculate_final_price

def test_calculate_final_price_invalid_input():
    expected = {"final_usd": 0, "base_usd": 0, "profit_usd": 0, "margin_tier": 0}

    assert calculate_final_price(0, "CNY") == expected
    assert calculate_final_price(-50, "CNY") == expected
    assert calculate_final_price("invalid", "CNY") == expected
    assert calculate_final_price(None, "CNY") == expected

def test_calculate_final_price_cny_tier_1():
    # val < 100
    res = calculate_final_price(50, "CNY")
    assert res["margin_tier"] == 2.2
    assert res["base_usd"] == round(50 / 7.2, 2)
    assert res["final_usd"] > 0
    assert res["profit_usd"] > 0

def test_calculate_final_price_cny_tier_2():
    # 100 <= val < 300
    res = calculate_final_price(150, "CNY")
    assert res["margin_tier"] == 1.8
    assert res["base_usd"] == round(150 / 7.2, 2)
    assert res["final_usd"] > 0
    assert res["profit_usd"] > 0

def test_calculate_final_price_cny_tier_3():
    # 300 <= val < 600
    res = calculate_final_price(450, "CNY")
    assert res["margin_tier"] == 1.6
    assert res["base_usd"] == round(450 / 7.2, 2)
    assert res["final_usd"] > 0
    assert res["profit_usd"] > 0

def test_calculate_final_price_cny_tier_4():
    # val >= 600
    res = calculate_final_price(1200, "CNY")
    assert res["margin_tier"] == 1.4
    assert res["base_usd"] == round(1200 / 7.2, 2)
    assert res["final_usd"] > 0
    assert res["profit_usd"] > 0
