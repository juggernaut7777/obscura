import pytest
from unittest.mock import patch
import sys
from goal2_sourcing_engine.voice_generator import safe_print

def test_safe_print_happy_path():
    with patch('builtins.print') as mock_print:
        safe_print("hello world")
        mock_print.assert_called_once_with("hello world")

def test_safe_print_unicode_error_recovery():
    with patch('builtins.print') as mock_print:
        # First call raises UnicodeEncodeError, second succeeds
        mock_print.side_effect = [UnicodeEncodeError('ascii', 'hello', 0, 1, 'mock error'), None]

        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'ascii'
            safe_print("hello")

        assert mock_print.call_count == 2
        # Check what the second call to print was
        # msg is 'hello'
        # encode('utf-8', 'replace').decode('ascii', 'replace')
        # 'hello'.encode('utf-8') -> b'hello'
        # b'hello'.decode('ascii') -> 'hello'
        mock_print.assert_called_with("hello")

def test_safe_print_total_failure():
    with patch('builtins.print') as mock_print:
        # First call raises UnicodeEncodeError, second raises generic Exception, third succeeds
        mock_print.side_effect = [
            UnicodeEncodeError('ascii', 'hello', 0, 1, 'mock error'),
            Exception('some other error'),
            None
        ]

        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'ascii'
            safe_print("hello")

        assert mock_print.call_count == 3
        mock_print.assert_called_with("[Print Error] Unable to encode output print message.")
