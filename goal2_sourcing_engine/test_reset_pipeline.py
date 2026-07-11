import os
import shutil
import pytest
from goal2_sourcing_engine.reset_pipeline import clear_directory

def test_clear_directory_success(tmp_path):
    # Setup: Create a file and a subdirectory
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("dummy")

    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    sub_file_path = dir_path / "sub_file.txt"
    sub_file_path.write_text("sub dummy")

    # Pre-checks
    assert os.path.exists(str(file_path))
    assert os.path.exists(str(dir_path))

    # Execute
    clear_directory(str(tmp_path))

    # Assertion
    assert os.path.exists(str(tmp_path))
    assert len(os.listdir(str(tmp_path))) == 0

def test_clear_directory_not_exists():
    # Should not raise an error
    clear_directory("/path/that/does/not/exist/9999")

def test_clear_directory_exception(tmp_path, mocker):
    # Setup
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("dummy")

    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    # Mock exceptions for os.remove and shutil.rmtree
    mocker.patch("goal2_sourcing_engine.reset_pipeline.os.remove", side_effect=Exception("Mocked File Deletion Error"))
    mocker.patch("goal2_sourcing_engine.reset_pipeline.shutil.rmtree", side_effect=Exception("Mocked Dir Deletion Error"))

    # Execute - Should handle the exceptions and not crash
    clear_directory(str(tmp_path))

    # The files should still exist because deletion failed
    assert os.path.exists(str(file_path))
    assert os.path.exists(str(dir_path))
