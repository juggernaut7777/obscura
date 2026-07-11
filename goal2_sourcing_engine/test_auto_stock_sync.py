import pytest
from unittest.mock import patch

from goal2_sourcing_engine.auto_stock_sync import load_current_products

def test_load_current_products_corrupted_json():
    """Test that load_current_products falls back to an empty list when DEMO_PRODUCTS JSON is corrupted."""
    corrupted_content = """
    export const DEMO_PRODUCTS = [
        { "id": "p1", "name": "Broken JSON"
        MISSING BRACE AND QUOTES
    ];

    export const COLLECTIONS = [{"id": "c1"}];
    export const DEMO_OUTFITS = [{"id": "o1"}];
    """

    with patch('goal2_sourcing_engine.auto_stock_sync.PRODUCTS_FILE') as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = corrupted_content

        products, collections_raw, outfits_raw = load_current_products()

        # Products should fallback to [] because of JSONDecodeError
        assert products == []
        assert collections_raw == '[{"id": "c1"}]'
        assert outfits_raw == '[{"id": "o1"}]'

def test_load_current_products_valid_json():
    """Test that load_current_products correctly parses valid JSON."""
    valid_content = """
    export const DEMO_PRODUCTS = [{"id": "p1", "name": "Valid Product"}];
    export const COLLECTIONS = [{"id": "c1"}];
    export const DEMO_OUTFITS = [{"id": "o1"}];
    """

    with patch('goal2_sourcing_engine.auto_stock_sync.PRODUCTS_FILE') as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = valid_content

        products, collections_raw, outfits_raw = load_current_products()

        assert products == [{"id": "p1", "name": "Valid Product"}]
        assert collections_raw == '[{"id": "c1"}]'
        assert outfits_raw == '[{"id": "o1"}]'

def test_load_current_products_file_not_exists():
    """Test behavior when products.js does not exist."""
    with patch('goal2_sourcing_engine.auto_stock_sync.PRODUCTS_FILE') as mock_file:
        mock_file.exists.return_value = False

        products, collections_raw, outfits_raw = load_current_products()

        assert products == []
        assert collections_raw == "[]"
        assert outfits_raw == "[]"
