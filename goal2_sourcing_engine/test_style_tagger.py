import pytest
from style_tagger import _keyword_tag

def test_keyword_tag_women_skirt():
    result = _keyword_tag("Women's Pleated Mini Skirt", 150.0)
    assert result["gender"] == "women"
    assert result["category"] == "bottom"
    assert result["sub_category"] == "skirt"
    assert result["niche"] == "elegant"
    assert "top" in result["compatible_with"]

def test_keyword_tag_men_streetwear():
    result = _keyword_tag("Supreme Men's Box Logo Hoodie", 800.0)
    assert result["gender"] == "men"
    assert result["category"] == "top"
    assert result["sub_category"] == "hoodie"
    assert result["niche"] == "streetwear"
    assert "cargo_pants" in result["compatible_with"]

def test_keyword_tag_unisex_athleisure():
    result = _keyword_tag("Running Tracksuit Set", 200.0)
    assert result["gender"] == "unisex"
    assert result["category"] == "set"
    assert result["sub_category"] == "set"
    assert result["niche"] == "athleisure"
    assert result["compatible_with"] == []

def test_keyword_tag_fallback():
    result = _keyword_tag("Unknown Item XYZ", 10.0)
    assert result["gender"] == "unisex"
    assert result["category"] == "top"
    assert result["sub_category"] == "tee"
    assert result["niche"] == "basics"
