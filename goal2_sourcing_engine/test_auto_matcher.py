import pytest
from auto_matcher import score_pair

def test_score_pair_valid_categories():
    """Test that valid category combinations return a score > 0."""
    assert score_pair({"category": "top"}, {"category": "bottom"}) > 0
    assert score_pair({"category": "bottom"}, {"category": "top"}) > 0
    assert score_pair({"category": "bottom"}, {"category": "outerwear"}) > 0
    assert score_pair({"category": "outerwear"}, {"category": "top"}) > 0
    assert score_pair({"category": "outerwear"}, {"category": "bottom"}) > 0

def test_score_pair_invalid_categories():
    """Test that invalid category combinations return 0 (hard block)."""
    assert score_pair({"category": "top"}, {"category": "top"}) == 0
    assert score_pair({"category": "bottom"}, {"category": "bottom"}) == 0
    assert score_pair({"category": "top"}, {"category": "outerwear"}) == 0

def test_score_pair_solo_categories():
    """Test that solo categories (shoes, accessory, dress, set) always return 0."""
    solo_categories = ["shoes", "accessory", "dress", "set"]
    for cat in solo_categories:
        assert score_pair({"category": cat}, {"category": "top"}) == 0
        assert score_pair({"category": cat}, {"category": "bottom"}) == 0
        assert score_pair({"category": "top"}, {"category": cat}) == 0
        assert score_pair({"category": "bottom"}, {"category": cat}) == 0

def test_score_pair_missing_or_unknown_categories():
    """Test behavior with missing or unknown categories."""
    assert score_pair({}, {"category": "top"}) == 0
    assert score_pair({"category": "top"}, {}) == 0
    assert score_pair({}, {}) == 0
    assert score_pair({"category": "unknown_cat"}, {"category": "top"}) == 0
    assert score_pair({"category": "top"}, {"category": "unknown_cat"}) == 0
