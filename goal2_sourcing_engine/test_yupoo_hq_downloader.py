import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader import download_yupoo_album_hq

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
def test_successful_download(mock_get):
    mock_resp = MagicMock()
    mock_resp.text = '''
        <html>
            <body>
                <div class="showalbum_item">
                    <img data-src="/small/image1.jpg">
                </div>
                <div class="showalbum_item">
                    <img src="//yupoo.com/medium/image2.png">
                </div>
            </body>
        </html>
    '''

    mock_img_resp1 = MagicMock()
    mock_img_resp1.content = b"fake_image_data_1"

    mock_img_resp2 = MagicMock()
    mock_img_resp2.content = b"fake_image_data_2"

    mock_get.side_effect = [mock_resp, mock_img_resp1, mock_img_resp2]

    with tempfile.TemporaryDirectory() as temp_dir:
        download_yupoo_album_hq("https://example.yupoo.com/albums/123", output_dir=temp_dir)

        # Verify files were created
        files = os.listdir(temp_dir)
        assert len(files) == 2
        assert "image1.jpg" in files
        assert "image2.png" in files

        # Check that requests were made to the expected URLs (yupoo.com checks)
        expected_urls = [
            "https://example.yupoo.com/albums/123",
            "https://example.yupoo.com/big/image1.jpg",
            "https://yupoo.com/big/image2.png"
        ]

        called_urls = [call[0][0] for call in mock_get.call_args_list]
        for url in expected_urls:
            assert url in called_urls

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
def test_fallback_to_generic_img_tags(mock_get):
    mock_resp = MagicMock()
    # No showalbum_item div, but it has generic img tags
    mock_resp.text = '''
        <html>
            <body>
                <div class="not_showalbum_item">
                    <img data-src="https://yupoo.com/small/image3.jpg">
                </div>
            </body>
        </html>
    '''

    mock_img_resp = MagicMock()
    mock_img_resp.content = b"fake_image_data_3"

    mock_get.side_effect = [mock_resp, mock_img_resp]

    with tempfile.TemporaryDirectory() as temp_dir:
        download_yupoo_album_hq("https://example.yupoo.com/albums/456", output_dir=temp_dir)

        files = os.listdir(temp_dir)
        assert len(files) == 1
        assert "image3.jpg" in files

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
def test_skip_non_yupoo_images(mock_get):
    mock_resp = MagicMock()
    # Provide one Yupoo image and one non-Yupoo image
    mock_resp.text = '''
        <html>
            <body>
                <div class="showalbum_item">
                    <img data-src="https://yupoo.com/big/image.jpg">
                </div>
                <div class="showalbum_item">
                    <img data-src="https://other.com/image.jpg">
                </div>
            </body>
        </html>
    '''

    mock_img_resp = MagicMock()
    mock_img_resp.content = b"fake_image_data"

    mock_get.side_effect = [mock_resp, mock_img_resp]

    with tempfile.TemporaryDirectory() as temp_dir:
        download_yupoo_album_hq("https://example.yupoo.com/albums/789", output_dir=temp_dir)

        files = os.listdir(temp_dir)
        assert len(files) == 1
        assert "image.jpg" in files

        called_urls = [call[0][0] for call in mock_get.call_args_list]
        assert "https://other.com/image.jpg" not in called_urls

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
def test_album_access_error(mock_get, capsys):
    # Simulate album page request raising an exception
    mock_get.side_effect = Exception("Connection error")

    with tempfile.TemporaryDirectory() as temp_dir:
        download_yupoo_album_hq("https://example.yupoo.com/albums/999", output_dir=temp_dir)

        files = os.listdir(temp_dir)
        assert len(files) == 0

        captured = capsys.readouterr()
        assert "Error accessing album: Connection error" in captured.out

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
def test_individual_image_download_error(mock_get, capsys):
    mock_resp = MagicMock()
    mock_resp.text = '''
        <html>
            <body>
                <div class="showalbum_item">
                    <img data-src="https://yupoo.com/big/image_fail.jpg">
                </div>
                <div class="showalbum_item">
                    <img data-src="https://yupoo.com/big/image_success.jpg">
                </div>
            </body>
        </html>
    '''

    mock_img_resp_fail = MagicMock()
    mock_img_resp_fail.raise_for_status.side_effect = Exception("Image not found")

    mock_img_resp_success = MagicMock()
    mock_img_resp_success.content = b"fake_image_data_success"

    mock_get.side_effect = [mock_resp, mock_img_resp_fail, mock_img_resp_success]

    with tempfile.TemporaryDirectory() as temp_dir:
        download_yupoo_album_hq("https://example.yupoo.com/albums/err", output_dir=temp_dir)

        files = os.listdir(temp_dir)
        # Should only download the successful one
        assert len(files) == 1
        assert "image_success.jpg" in files

        captured = capsys.readouterr()
        assert "Failed to download https://yupoo.com/big/image_fail.jpg" in captured.out
