"""
Test YouTube Extractor functionality
"""

import sys
import os
import unittest
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from summary.extractors.youtube import YouTubeExtractor


class TestYouTubeExtractor(unittest.TestCase):
    """Test cases for YouTubeExtractor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = YouTubeExtractor()

    def test_extract_video_id_standard_url(self):
        """Test extraction from standard YouTube watch URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = self.extractor.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_short_url(self):
        """Test extraction from youtu.be short URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = self.extractor.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_embed_url(self):
        """Test extraction from embed URL"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = self.extractor.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_shorts_url(self):
        """Test extraction from YouTube shorts"""
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        video_id = self.extractor.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_invalid_url(self):
        """Test extraction returns None for invalid URL"""
        url = "https://example.com/watch?v=123"
        video_id = self.extractor.extract_video_id(url)
        self.assertIsNone(video_id)

    def test_extract_video_id_no_url(self):
        """Test extraction returns None for empty string"""
        url = ""
        video_id = self.extractor.extract_video_id(url)
        self.assertIsNone(video_id)

    @patch.object(YouTubeExtractor, "get_transcript")
    def test_extract_method(self, mock_get_transcript):
        """Test main extract method"""
        mock_get_transcript.return_value = {
            "text": "Test transcript",
            "language": "en",
            "video_id": "dQw4w9WgXcQ",
            "success": True,
        }

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = self.extractor.extract(url)

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "Test transcript")
        self.assertEqual(result["video_id"], "dQw4w9WgXcQ")

    def test_extract_method_invalid_url(self):
        """Test extract method with invalid URL"""
        url = "https://invalid-url.com"
        result = self.extractor.extract(url)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Invalid YouTube URL")
        self.assertEqual(result["text"], "")

    def test_multiple_url_patterns(self):
        """Test various YouTube URL patterns"""
        test_cases = [
            ("https://youtube.com/watch?v=ABC123abc12", "ABC123abc12"),
            ("https://www.youtube.com/watch?v=ABC123abc12", "ABC123abc12"),
            ("https://www.youtube.com/watch?si=share123&v=ABC123abc12&feature=youtu.be", "ABC123abc12"),
            ("https://youtube.com/v/ABC123abc12", "ABC123abc12"),
            ("https://youtu.be/ABC123abc12", "ABC123abc12"),
            ("https://youtu.be/ABC123abc12?si=share123", "ABC123abc12"),
            ("https://www.youtube.com/shorts/ABC123abc12", "ABC123abc12"),
            ("https://m.youtube.com/shorts/ABC123abc12", "ABC123abc12"),
            ("https://www.youtube.com/live/ABC123abc12?si=share123", "ABC123abc12"),
            ("https://www.youtube.com/embed/ABC123abc12", "ABC123abc12"),
        ]

        for url, expected_id in test_cases:
            with self.subTest(url=url):
                result = self.extractor.extract_video_id(url)
                self.assertEqual(result, expected_id, f"Failed for URL: {url}")


class TestYouTubeExtractorIntegration(unittest.TestCase):
    """Integration tests for YouTubeExtractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = YouTubeExtractor()

    @patch.object(YouTubeExtractor, "_get_transcript_ytapi")
    def test_get_transcript_success(self, mock_get_transcript_ytapi):
        """Test successful transcript retrieval"""
        mock_get_transcript_ytapi.return_value = {
            "text": "This is a test transcript text This is a test transcript text",
            "language": "en",
            "video_id": "dQw4w9WgXcQ",
            "success": True,
        }

        result = self.extractor.get_transcript("dQw4w9WgXcQ")

        self.assertTrue(result["success"])
        self.assertEqual(
            result["text"],
            "This is a test transcript text This is a test transcript text",
        )
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["video_id"], "dQw4w9WgXcQ")

    @patch.object(YouTubeExtractor, "_get_transcript_ytdlp", side_effect=Exception("yt-dlp also failed"))
    @patch.object(YouTubeExtractor, "_get_transcript_direct", side_effect=Exception("direct failed"))
    @patch.object(YouTubeExtractor, "_get_transcript_ytapi", side_effect=Exception("TranscriptsDisabled"))
    def test_get_transcript_disabled(self, mock_ytapi, mock_direct, mock_ytdlp):
        """Test transcript when disabled"""
        result = self.extractor.get_transcript("dQw4w9WgXcQ")

        self.assertFalse(result["success"])
        self.assertIn("disabled", result["error"].lower())

    @patch.object(YouTubeExtractor, "_get_transcript_ytdlp", side_effect=Exception("yt-dlp also failed"))
    @patch.object(YouTubeExtractor, "_get_transcript_direct", side_effect=Exception("direct failed"))
    @patch.object(YouTubeExtractor, "_get_transcript_ytapi", side_effect=Exception("VideoUnavailable"))
    def test_get_transcript_unavailable(self, mock_ytapi, mock_direct, mock_ytdlp):
        """Test transcript when video unavailable"""
        result = self.extractor.get_transcript("dQw4w9WgXcQ")

        self.assertFalse(result["success"])
        self.assertIn("unavailable", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
