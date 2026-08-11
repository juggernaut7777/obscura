import pytest
from luxury_caption_generator import sanitize_for_tiktok, BRAND_CODES

def test_sanitize_for_tiktok_basic():
    """Test basic replacement of a single brand name."""
    text = "Check out my new Louis Vuitton bag!"
    expected = "Check out my new the LV pattern ones bag!"
    assert sanitize_for_tiktok(text) == expected

def test_sanitize_for_tiktok_case_insensitivity():
    """Test that replacements are case-insensitive."""
    text = "I love GUCCI and dior."
    expected = "I love the GG ones and the ones with the oblique print."
    assert sanitize_for_tiktok(text) == expected

def test_sanitize_for_tiktok_multiple_brands():
    """Test replacing multiple different brands in the same text."""
    text = "Selling Nike, Jordan, and Yeezy shoes."
    expected = "Selling swoosh ones, the J's, and the foam ones shoes."
    assert sanitize_for_tiktok(text) == expected

def test_sanitize_for_tiktok_no_brands():
    """Test that text without brands is unchanged."""
    text = "This is a regular sentence with no designer names."
    assert sanitize_for_tiktok(text) == text

def test_sanitize_for_tiktok_empty_string():
    """Test with an empty string."""
    assert sanitize_for_tiktok("") == ""

def test_sanitize_for_tiktok_special_characters():
    """Test string with special characters around the brand."""
    text = "Wow! **Balenciaga** is expensive! (Prada too)"
    expected = "Wow! **the chunky ones** is expensive! (the triangle logo ones too)"
    assert sanitize_for_tiktok(text) == expected

def test_sanitize_for_tiktok_partial_word():
    """Test whether it replaces partial matches (it currently does with regex, which is expected behavior)."""
    text = "I have an off-white colored shirt."
    expected = "I have an the zip-tie ones colored shirt."
    assert sanitize_for_tiktok(text) == expected
