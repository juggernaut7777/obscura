import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image

from style_tagger import _gemini_vision_tag

def create_dummy_image(tmp_path):
    img_path = tmp_path / "test_image.jpg"
    img = Image.new('RGB', (10, 10), color = 'red')
    img.save(img_path)
    return img_path

def test_gemini_vision_tag_error_litellm(tmp_path):
    """Test that _gemini_vision_tag safely handles litellm_router exceptions."""
    img_path = create_dummy_image(tmp_path)

    # We use a context manager to prevent global state leaks
    with patch('style_tagger.shared_router.get_chat_completion_sync') as mock_router:
        mock_router.side_effect = Exception("Mocked API Error")

        result = _gemini_vision_tag(img_path, "Test Product")

        # Verify the result is handled safely (returns empty dict or fallback)
        assert isinstance(result, dict)
        assert result == {}

        # Verify the mock was called
        mock_router.assert_called_once()
