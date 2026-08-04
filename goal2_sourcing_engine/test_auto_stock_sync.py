import json
from unittest.mock import patch, mock_open
from goal2_sourcing_engine.auto_stock_sync import load_supplier_mappings, save_supplier_mappings, SUPPLIER_MAPPINGS_FILE

def test_load_supplier_mappings_exists():
    mock_data = {"product_1": {"source_url": "http://example.com", "stock_status": {}}}
    mock_json = json.dumps(mock_data)

    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True

        with patch("builtins.open", mock_open(read_data=mock_json)) as m_open:
            result = load_supplier_mappings()

            # Verify open was called correctly
            m_open.assert_called_once_with(SUPPLIER_MAPPINGS_FILE, "r", encoding="utf-8")

            # Verify the result is as expected
            assert result == mock_data

def test_load_supplier_mappings_not_exists():
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = load_supplier_mappings()

        # Verify an empty dict is returned
        assert result == {}

def test_save_supplier_mappings():
    mappings_to_save = {"product_2": {"source_url": "http://test.com"}}

    with patch("builtins.open", mock_open()) as m_open:
        with patch("json.dump") as mock_json_dump:
            save_supplier_mappings(mappings_to_save)

            # Verify open was called correctly
            m_open.assert_called_once_with(SUPPLIER_MAPPINGS_FILE, "w", encoding="utf-8")

            # Verify json.dump was called correctly
            mock_json_dump.assert_called_once_with(
                mappings_to_save,
                m_open(),
                indent=2,
                ensure_ascii=False
            )
