import json
from unittest.mock import MagicMock, patch
from goal2_sourcing_engine.order_fulfillment import reverse_map_to_chinese

def test_missing_supplier_mappings_file():
    with patch("goal2_sourcing_engine.order_fulfillment.SUPPLIER_MAPPINGS_FILE") as mock_file:
        mock_file.exists.return_value = False
        result = reverse_map_to_chinese("prod-1", "Black", "L")
        assert result is None

def test_invalid_json_in_supplier_mappings_file():
    with patch("goal2_sourcing_engine.order_fulfillment.SUPPLIER_MAPPINGS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "invalid json"
        result = reverse_map_to_chinese("prod-1", "Black", "L")
        assert result is None

def test_product_id_missing_in_mappings():
    with patch("goal2_sourcing_engine.order_fulfillment.SUPPLIER_MAPPINGS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps({"prod-2": {}})
        result = reverse_map_to_chinese("prod-1", "Black", "L")
        assert result is None

def test_exact_match():
    mock_data = {
        "prod-1": {
            "source_url": "http://example.com/1",
            "platform": "weidian",
            "item_id": "123",
            "cost_cny": 100,
            "seller": {"name": "Test Seller"},
            "variant_mappings": {
                "colors": {"Black": "黑色", "White": "白色"},
                "sizes": {"L": "L码", "M": "M码"}
            }
        }
    }
    with patch("goal2_sourcing_engine.order_fulfillment.SUPPLIER_MAPPINGS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(mock_data)
        result = reverse_map_to_chinese("prod-1", "Black", "L")

        assert result is not None
        assert result["source_url"] == "http://example.com/1"
        assert result["platform"] == "weidian"
        assert result["item_id"] == "123"
        assert result["chinese_color"] == "黑色"
        assert result["chinese_size"] == "L码"
        assert result["english_color"] == "Black"
        assert result["english_size"] == "L"
        assert result["cost_cny"] == 100
        assert result["seller_name"] == "Test Seller"

def test_case_insensitive_match():
    mock_data = {
        "prod-1": {
            "variant_mappings": {
                "colors": {"Black": "黑色"},
                "sizes": {"Large": "L码"}
            }
        }
    }
    with patch("goal2_sourcing_engine.order_fulfillment.SUPPLIER_MAPPINGS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(mock_data)

        result = reverse_map_to_chinese("prod-1", "bLAcK", "laRGe")

        assert result is not None
        assert result["chinese_color"] == "黑色"
        assert result["chinese_size"] == "L码"

def test_no_match_returns_empty_string_for_chinese():
    mock_data = {
        "prod-1": {
            "variant_mappings": {
                "colors": {"Black": "黑色"},
                "sizes": {"L": "L码"}
            }
        }
    }
    with patch("goal2_sourcing_engine.order_fulfillment.SUPPLIER_MAPPINGS_FILE") as mock_file:
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = json.dumps(mock_data)

        result = reverse_map_to_chinese("prod-1", "Red", "XL")

        assert result is not None
        assert result["chinese_color"] == ""
        assert result["chinese_size"] == ""
        assert result["english_color"] == "Red"
        assert result["english_size"] == "XL"
