import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader import download_yupoo_album_hq

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.os.makedirs")
@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.os.path.exists", return_value=False)
def test_download_yupoo_album_hq_happy_path(mock_exists, mock_makedirs, mock_get):
    mock_resp = MagicMock()
    mock_resp.text = '''
        <html>
            <body>
                <div class="showalbum_item">
                    <img data-src="//photo.yupoo.com/someuser/123/small/image1.jpg">
                </div>
            </body>
        </html>
    '''
    mock_img_resp = MagicMock()
    mock_img_resp.content = b"fake_image_data"

    mock_get.side_effect = [mock_resp, mock_img_resp]

    with patch("builtins.open", mock_open()) as mock_file:
        download_yupoo_album_hq("https://someuser.x.yupoo.com/albums/123", "test_output")

        mock_makedirs.assert_called_once_with("test_output")
        mock_file.assert_called_once_with(os.path.join("test_output", "image1.jpg"), 'wb')
        mock_file().write.assert_called_once_with(b"fake_image_data")

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.os.makedirs")
@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.os.path.exists", return_value=False)
def test_download_yupoo_album_hq_fallback(mock_exists, mock_makedirs, mock_get):
    mock_resp = MagicMock()
    mock_resp.text = '''
        <html>
            <body>
                <img data-src="//photo.yupoo.com/someuser/123/small/image1.jpg">
            </body>
        </html>
    '''
    mock_img_resp = MagicMock()
    mock_img_resp.content = b"fake_image_data"

    mock_get.side_effect = [mock_resp, mock_img_resp]

    with patch("builtins.open", mock_open()) as mock_file:
        download_yupoo_album_hq("https://someuser.x.yupoo.com/albums/123", "test_output")

        mock_makedirs.assert_called_once_with("test_output")
        mock_file.assert_called_once_with(os.path.join("test_output", "image1.jpg"), 'wb')
        mock_file().write.assert_called_once_with(b"fake_image_data")

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
def test_download_yupoo_album_hq_http_error(mock_get, capsys):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("HTTP Error")
    mock_get.return_value = mock_resp

    download_yupoo_album_hq("https://someuser.x.yupoo.com/albums/123", "test_output")

    captured = capsys.readouterr()
    assert "[!] Error accessing album: HTTP Error" in captured.out

@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.requests.get")
@patch("goal2_sourcing_engine._archive.replica_yupoo.yupoo_hq_downloader.os.path.exists", return_value=True)
def test_download_yupoo_album_hq_skip_non_yupoo(mock_exists, mock_get, capsys):
    mock_resp = MagicMock()
    mock_resp.text = '''
        <html>
            <body>
                <div class="showalbum_item">
                    <img data-src="//other-domain.com/image.jpg">
                </div>
            </body>
        </html>
    '''
    mock_get.return_value = mock_resp

    download_yupoo_album_hq("https://someuser.x.yupoo.com/albums/123", "test_output")

    captured = capsys.readouterr()
    assert "Successfully downloaded 0 HQ images" in captured.out
