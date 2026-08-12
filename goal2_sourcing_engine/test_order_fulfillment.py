import json
import pytest
from unittest.mock import patch
from pathlib import Path

from order_fulfillment import reverse_map_to_chinese

@pytest.fixture
def mock_mappings_file(tmp_path):
    mock_file = tmp_path / "supplier_mappings.json"
    mock_data = {
        "heavy-vintage-wash-hoodie-abc123": {
            "source_url": "https://weidian.com/item.html?itemID=7543891234",
            "platform": "weidian",
            "item_id": "7543891234",
            "cost_cny": 189,
            "seller": {"name": "Vintage Wash Co."},
            "variant_mappings": {
                "colors": {
                    "Black": "黑色",
                    "Grey": "灰色"
                },
                "sizes": {
                    "L": "L码",
                    "XL": "XL码"
                }
            }
        }
    }
    mock_file.write_text(json.dumps(mock_data), encoding="utf-8")
    return mock_file

def test_reverse_map_exact_match(mock_mappings_file):
    with patch("order_fulfillment.SUPPLIER_MAPPINGS_FILE", mock_mappings_file):
        result = reverse_map_to_chinese("heavy-vintage-wash-hoodie-abc123", "Black", "L")

        assert result is not None
        assert result["chinese_color"] == "黑色"
        assert result["chinese_size"] == "L码"
        assert result["source_url"] == "https://weidian.com/item.html?itemID=7543891234"
        assert result["cost_cny"] == 189
        assert result["seller_name"] == "Vintage Wash Co."

def test_reverse_map_case_insensitive(mock_mappings_file):
    with patch("order_fulfillment.SUPPLIER_MAPPINGS_FILE", mock_mappings_file):
        result = reverse_map_to_chinese("heavy-vintage-wash-hoodie-abc123", "black", "l")

        assert result is not None
        assert result["chinese_color"] == "黑色"
        assert result["chinese_size"] == "L码"

def test_reverse_map_product_not_found(mock_mappings_file):
    with patch("order_fulfillment.SUPPLIER_MAPPINGS_FILE", mock_mappings_file):
        result = reverse_map_to_chinese("non-existent-product", "Black", "L")
        assert result is None

def test_reverse_map_missing_file(tmp_path):
    missing_file = tmp_path / "does_not_exist.json"
    with patch("order_fulfillment.SUPPLIER_MAPPINGS_FILE", missing_file):
        result = reverse_map_to_chinese("heavy-vintage-wash-hoodie-abc123", "Black", "L")
        assert result is None

def test_reverse_map_invalid_json(tmp_path):
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("invalid json {", encoding="utf-8")

    with patch("order_fulfillment.SUPPLIER_MAPPINGS_FILE", invalid_file):
        result = reverse_map_to_chinese("heavy-vintage-wash-hoodie-abc123", "Black", "L")
        assert result is None
