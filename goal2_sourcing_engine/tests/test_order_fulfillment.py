import pytest
from goal2_sourcing_engine.order_fulfillment import estimate_weight

@pytest.mark.parametrize(
    "category, quantity, expected",
    [
        ("hoodie", 1, 0.6),
        ("red hoodie", 1, 0.6),
        ("sneakers", 2, 1.8),
        ("unknown", 3, 1.2),
        ("", 1, 0.4),
        (None, 2, 0.8),
    ]
)
def test_estimate_weight(category, quantity, expected):
    """Test happy path scenarios for known categories."""
    assert estimate_weight(category, quantity) == pytest.approx(expected)
