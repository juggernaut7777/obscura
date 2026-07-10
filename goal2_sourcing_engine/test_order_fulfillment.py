import pytest
from goal2_sourcing_engine.order_fulfillment import ddp_shipping_cost, DDP_SHIPPING_RATE_PER_KG, DDP_MIN_SHIPPING

def test_ddp_shipping_cost_zero_weight():
    """Test with zero weight, should return minimum shipping cost."""
    assert ddp_shipping_cost(0) == DDP_MIN_SHIPPING

def test_ddp_shipping_cost_below_minimum():
    """Test with a weight that yields a cost below the minimum."""
    weight = 1.0  # 1.0 * 12.0 = 12.0 < 15.0
    assert ddp_shipping_cost(weight) == DDP_MIN_SHIPPING

def test_ddp_shipping_cost_exact_minimum():
    """Test with a weight that yields exactly the minimum cost."""
    weight = 1.25  # 1.25 * 12.0 = 15.0
    assert ddp_shipping_cost(weight) == DDP_MIN_SHIPPING

def test_ddp_shipping_cost_above_minimum():
    """Test with a weight that yields a cost above the minimum."""
    weight = 2.0  # 2.0 * 12.0 = 24.0 > 15.0
    expected_cost = 2.0 * DDP_SHIPPING_RATE_PER_KG
    assert ddp_shipping_cost(weight) == expected_cost

def test_ddp_shipping_cost_large_weight():
    """Test with a large weight to ensure scaling works correctly."""
    weight = 10.5  # 10.5 * 12.0 = 126.0
    expected_cost = 10.5 * DDP_SHIPPING_RATE_PER_KG
    assert ddp_shipping_cost(weight) == expected_cost
