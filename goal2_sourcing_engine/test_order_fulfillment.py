import pytest
from goal2_sourcing_engine.order_fulfillment import estimate_weight, ITEM_WEIGHTS

def test_estimate_weight_exact_match():
    assert estimate_weight("hoodie") == ITEM_WEIGHTS["hoodie"]
    assert estimate_weight("sneakers") == ITEM_WEIGHTS["sneakers"]

def test_estimate_weight_case_insensitivity():
    assert estimate_weight("HOODIE") == ITEM_WEIGHTS["hoodie"]
    assert estimate_weight("T-Shirt") == ITEM_WEIGHTS["t-shirt"]
    assert estimate_weight("SnEaKeRs") == ITEM_WEIGHTS["sneakers"]

def test_estimate_weight_substring_match():
    # Should match "hoodie" in "vintage wash hoodie"
    assert estimate_weight("vintage wash hoodie") == ITEM_WEIGHTS["hoodie"]
    # Should match "jeans" in "black jeans"
    assert estimate_weight("black jeans") == ITEM_WEIGHTS["jeans"]

def test_estimate_weight_quantity_multiplier():
    assert estimate_weight("sneakers", 2) == ITEM_WEIGHTS["sneakers"] * 2
    assert estimate_weight("shirt", 5) == ITEM_WEIGHTS["shirt"] * 5
    assert estimate_weight("unknown category", 3) == ITEM_WEIGHTS["default"] * 3

def test_estimate_weight_edge_cases():
    # None should fall back to default
    assert estimate_weight(None) == ITEM_WEIGHTS["default"]
    # Empty string should fall back to default
    assert estimate_weight("") == ITEM_WEIGHTS["default"]
    # Unknown category should fall back to default
    assert estimate_weight("alien spacesuit") == ITEM_WEIGHTS["default"]

def test_estimate_weight_quantity_with_edge_cases():
    assert estimate_weight(None, 4) == ITEM_WEIGHTS["default"] * 4
    assert estimate_weight("", 2) == ITEM_WEIGHTS["default"] * 2
