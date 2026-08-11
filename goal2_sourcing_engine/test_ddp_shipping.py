import pytest
from order_fulfillment import ddp_shipping_cost

def test_ddp_shipping_cost_zero():
    # Since cost = total_weight_kg * DDP_SHIPPING_RATE_PER_KG (12.0)
    # 0 <= 0 is false, it computes:
    # 0 * 12.0 = 0 -> max(0, 15.0) -> 15.0
    assert ddp_shipping_cost(0.0) == 15.0
    assert ddp_shipping_cost(-1.0) == 15.0

def test_ddp_shipping_cost_small():
    # 0.5kg -> 0.5 * 12.0 = 6.0 -> max(6.0, 15.0) -> 15.0
    assert ddp_shipping_cost(0.5) == 15.0

def test_ddp_shipping_cost_large():
    # 2.0kg -> 2.0 * 12.0 = 24.0 -> max(24.0, 15.0) -> 24.0
    assert ddp_shipping_cost(2.0) == 24.0

def test_ddp_shipping_cost_exact_min():
    # 1.25kg -> 1.25 * 12.0 = 15.0 -> max(15.0, 15.0) -> 15.0
    assert ddp_shipping_cost(1.25) == 15.0
