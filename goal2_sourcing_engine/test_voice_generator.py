import os
from unittest.mock import patch
from voice_generator import VoiceGenerator

def test_combine_video_audio_missing_video_path():
    generator = VoiceGenerator()

    # We want os.path.exists to return False for the video_path and True for the audio_path
    def mock_exists(path):
        if path == "missing_video.mp4":
            return False
        return True

    with patch('os.path.exists', side_effect=mock_exists):
        result = generator.combine_video_audio("missing_video.mp4", "valid_audio.mp3")

    assert result is None

def test_combine_video_audio_missing_audio_path():
    generator = VoiceGenerator()

    # We want os.path.exists to return True for the video_path and False for the audio_path
    def mock_exists(path):
        if path == "missing_audio.mp3":
            return False
        return True

    with patch('os.path.exists', side_effect=mock_exists):
        result = generator.combine_video_audio("valid_video.mp4", "missing_audio.mp3")

    assert result is None
