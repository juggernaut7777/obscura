import pytest
from pathlib import Path
from unittest.mock import patch

from style_tagger import _gemini_vision_tag

def test_gemini_vision_tag_error(tmp_path):
    # Setup a dummy image file
    image_path = tmp_path / "test_image.jpg"
    image_path.write_bytes(b"dummy image content")

    # Mock litellm router to raise an exception
    with patch("style_tagger.shared_router.get_chat_completion_sync", side_effect=Exception("Simulated Gemini API error")):
        result = _gemini_vision_tag(image_path, "Test Product")

        # When an error occurs, it should return an empty dict
        assert result == {}
