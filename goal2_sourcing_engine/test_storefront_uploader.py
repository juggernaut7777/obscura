from unittest.mock import patch, mock_open

import storefront_uploader

@patch("storefront_uploader.Path.exists")
@patch("builtins.open", new_callable=mock_open, read_data='{"product1": {"source_url": "http://example.com"}}')
def test_load_supplier_mappings_exists(mock_file, mock_exists):
    mock_exists.return_value = True

    result = storefront_uploader.load_supplier_mappings()

    assert result == {"product1": {"source_url": "http://example.com"}}

@patch("storefront_uploader.Path.exists")
def test_load_supplier_mappings_not_exists(mock_exists):
    mock_exists.return_value = False

    result = storefront_uploader.load_supplier_mappings()

    assert result == {}
