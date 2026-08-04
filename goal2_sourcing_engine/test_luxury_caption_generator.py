import pytest
from goal2_sourcing_engine.luxury_caption_generator import sanitize_for_tiktok

def test_sanitize_for_tiktok_basic():
    """Test standard brand replacement."""
    assert sanitize_for_tiktok("Buy this louis vuitton bag") == "Buy this the LV pattern ones bag"

def test_sanitize_for_tiktok_case_insensitive():
    """Test that brand replacement ignores case."""
    assert sanitize_for_tiktok("Get the LoUiS VuItToN shoes") == "Get the the LV pattern ones shoes"

def test_sanitize_for_tiktok_multiple():
    """Test replacing multiple different brands in one string."""
    assert sanitize_for_tiktok("louis vuitton and gucci") == "the LV pattern ones and the GG ones"

def test_sanitize_for_tiktok_no_brands():
    """Test string with no brands remains unchanged."""
    assert sanitize_for_tiktok("Just a regular bag") == "Just a regular bag"

def test_sanitize_for_tiktok_empty():
    """Test empty string."""
    assert sanitize_for_tiktok("") == ""

def test_sanitize_for_tiktok_substring():
    """Test that brands as substrings are NOT replaced (e.g., 'lv' in 'Silver')."""
    # Without word boundaries, 'lv' might match inside 'Silver'
    assert sanitize_for_tiktok("Silver") == "Silver"
    assert sanitize_for_tiktok("velvet") == "velvet"

def test_sanitize_for_tiktok_overlapping():
    """Test that overlapping brands don't double replace."""
    # 'louis vuitton' -> 'the LV pattern ones'.
    # The output contains 'LV'. If we process sequentially, 'lv' -> 'the monogram ones' might replace it!
    # Expected: "the LV pattern ones"
    assert sanitize_for_tiktok("louis vuitton") == "the LV pattern ones"

def test_sanitize_for_tiktok_punctuation():
    """Test matching at word boundaries next to punctuation."""
    assert sanitize_for_tiktok("Check out my Gucci!") == "Check out my the GG ones!"
    assert sanitize_for_tiktok("Gucci, Prada, and Dior.") == "the GG ones, the triangle logo ones, and the ones with the oblique print."
