import pytest
from goal2_sourcing_engine.luxury_caption_generator import sanitize_for_tiktok

def test_simple_replacement():
    assert sanitize_for_tiktok("I want gucci shoes") == "I want the GG ones shoes"
    assert sanitize_for_tiktok("Buying some nike.") == "Buying some swoosh ones."

def test_case_insensitive():
    assert sanitize_for_tiktok("GUCCI") == "the GG ones"
    assert sanitize_for_tiktok("Louis Vuitton") == "the LV pattern ones"
    assert sanitize_for_tiktok("bAlEnCiAgA") == "the chunky ones"

def test_multiple_brands():
    text = "I love prada and hermes."
    expected = "I love the triangle logo ones and the H belt ones."
    assert sanitize_for_tiktok(text) == expected

def test_word_boundaries():
    # 'lv' shouldn't match inside 'silver', 'pelvis'
    assert sanitize_for_tiktok("silver") == "silver"
    assert sanitize_for_tiktok("pelvis") == "pelvis"

    # 'dior' shouldn't match inside 'diorama'
    assert sanitize_for_tiktok("diorama") == "diorama"

    # ensure it still matches when punctuation is adjacent
    assert sanitize_for_tiktok("silver lv chain") == "silver the monogram ones chain"
    assert sanitize_for_tiktok("lv, dior, and gucci!") == "the monogram ones, the ones with the oblique print, and the GG ones!"

def test_overlapping_replacements():
    # "louis vuitton" translates to "the LV pattern ones"
    # if sequential, "the LV pattern ones" might have "LV" replaced again with "the monogram ones"
    # yielding "the the monogram ones pattern ones"
    assert sanitize_for_tiktok("louis vuitton") == "the LV pattern ones"

def test_no_brands_present():
    assert sanitize_for_tiktok("Just a regular sentence.") == "Just a regular sentence."
    assert sanitize_for_tiktok("") == ""
