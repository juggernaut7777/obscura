import pytest
from unittest.mock import patch
from goal2_sourcing_engine.agent_product_scraper import add_affiliate_link

MOCK_AFFILIATE_CODES = {
    "usfans": "usfans_code",
    "cnfans": "cnfans_code",
    "cssbuy": "cssbuy_code",
    "emptycode": "",
}

@patch("goal2_sourcing_engine.agent_product_scraper.AFFILIATE_CODES", MOCK_AFFILIATE_CODES)
def test_add_affiliate_link_no_query_params():
    product = {
        "source": "usfans",
        "productUrl": "https://example.com/product/123"
    }
    add_affiliate_link(product)
    assert product["affiliateUrl"] == "https://example.com/product/123?ref=usfans_code"

@patch("goal2_sourcing_engine.agent_product_scraper.AFFILIATE_CODES", MOCK_AFFILIATE_CODES)
def test_add_affiliate_link_with_query_params():
    product = {
        "source": "cnfans",
        "productUrl": "https://example.com/product?id=123"
    }
    add_affiliate_link(product)
    assert product["affiliateUrl"] == "https://example.com/product?id=123&ref=cnfans_code"

@patch("goal2_sourcing_engine.agent_product_scraper.AFFILIATE_CODES", MOCK_AFFILIATE_CODES)
def test_add_affiliate_link_unknown_source():
    product = {
        "source": "unknown_source",
        "productUrl": "https://example.com/product/123"
    }
    add_affiliate_link(product)
    assert product["affiliateUrl"] == "https://example.com/product/123"

@patch("goal2_sourcing_engine.agent_product_scraper.AFFILIATE_CODES", MOCK_AFFILIATE_CODES)
def test_add_affiliate_link_missing_keys():
    product = {}
    add_affiliate_link(product)
    assert product["affiliateUrl"] == ""

@patch("goal2_sourcing_engine.agent_product_scraper.AFFILIATE_CODES", MOCK_AFFILIATE_CODES)
def test_add_affiliate_link_empty_code():
    product = {
        "source": "emptycode",
        "productUrl": "https://example.com/product/123"
    }
    add_affiliate_link(product)
    assert product["affiliateUrl"] == "https://example.com/product/123"

@patch("goal2_sourcing_engine.agent_product_scraper.AFFILIATE_CODES", MOCK_AFFILIATE_CODES)
def test_add_affiliate_link_missing_url():
    product = {
        "source": "usfans"
    }
    add_affiliate_link(product)
    assert product["affiliateUrl"] == ""

@patch("goal2_sourcing_engine.agent_product_scraper.AFFILIATE_CODES", MOCK_AFFILIATE_CODES)
def test_add_affiliate_link_missing_source():
    product = {
        "productUrl": "https://example.com/product/123"
    }
    add_affiliate_link(product)
    assert product["affiliateUrl"] == "https://example.com/product/123"
