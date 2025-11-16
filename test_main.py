import pytest
from unittest.mock import patch, MagicMock
from main import get_video_info_from_url
import logging

# Suppress logging output during tests for cleaner console output
logging.getLogger().setLevel(logging.CRITICAL)

@pytest.fixture
def mock_yt_dlp():
    """Fixture to mock yt_dlp.YoutubeDL for tests."""
    with patch('main.yt_dlp.YoutubeDL') as mock_ydl_class:
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        yield mock_ydl_instance

def test_get_video_info_from_url_success(mock_yt_dlp):
    """
    Test that get_video_info_from_url correctly extracts video info
    for a valid YouTube URL.
    """
    # Configure the mock to return a specific info_dict
    mock_yt_dlp.extract_info.return_value = {
        'id': 'test_video_id',
        'title': 'Test Video Title with Special Chars!@#$',
        'webpage_url': 'https://www.youtube.com/watch?v=test_video_id'
    }

    url = "https://www.youtube.com/watch?v=test_video_id"
    result = get_video_info_from_url(url)

    # Assert that yt_dlp.YoutubeDL was called correctly
    mock_yt_dlp.extract_info.assert_called_once_with(url, download=False)

    # Assert the returned result is as expected
    assert result == {
        'video_id': 'test_video_id',
        'title': 'Test Video Title with Special Chars!@#$',
        'safe_folder_name': 'Test_Video_Title_with_Special_Chars',
    }

def test_get_video_info_from_url_invalid_url(mock_yt_dlp):
    """
    Test that get_video_info_from_url returns None for an invalid URL
    or when yt_dlp fails to extract info.
    """
    # Configure the mock to raise an exception or return an empty dict
    mock_yt_dlp.extract_info.side_effect = Exception("Simulated yt_dlp error")

    url = "https://www.youtube.com/watch?v=invalid_url"
    result = get_video_info_from_url(url)

    # Assert that yt_dlp.YoutubeDL was called
    mock_yt_dlp.extract_info.assert_called_once_with(url, download=False)

    # Assert the result is None
    assert result is None

def test_get_video_info_from_url_missing_info(mock_yt_dlp):
    """
    Test that get_video_info_from_url returns None if essential info (id/title) is missing.
    """
    # Configure the mock to return an info_dict missing 'id'
    mock_yt_dlp.extract_info.return_value = {
        'title': 'Test Video Title',
        'webpage_url': 'https://www.youtube.com/watch?v=test_video_id'
    }

    url = "https://www.youtube.com/watch?v=test_video_id"
    result = get_video_info_from_url(url)

    # Assert the result is None
    assert result is None

    # Configure the mock to return an info_dict missing 'title'
    mock_yt_dlp.extract_info.return_value = {
        'id': 'test_video_id',
        'webpage_url': 'https://www.youtube.com/watch?v=test_video_id'
    }
    result = get_video_info_from_url(url)
    assert result is None
