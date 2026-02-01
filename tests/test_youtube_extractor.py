"""
Test YouTube Extractor functionality
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

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
            ("https://youtube.com/watch?v=ABC123", "ABC123"),
            ("https://www.youtube.com/watch?v=ABC123", "ABC123"),
            ("https://youtube.com/v/ABC123", "ABC123"),
            ("https://youtu.be/ABC123", "ABC123"),
            ("https://www.youtube.com/shorts/ABC123", "ABC123"),
            ("https://www.youtube.com/embed/ABC123", "ABC123"),
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

    @patch("youtube_transcript_api.YouTubeTranscriptApi.fetch")
    def test_get_transcript_success(self, mock_fetch):
        """Test successful transcript retrieval"""
        # Mock transcript response
        mock_transcript = MagicMock()
        mock_snippet = MagicMock()
        mock_snippet.text = "This is a test transcript text"
        mock_transcript.snippets = [mock_snippet, mock_snippet]
        mock_transcript.language_code = "en"
        mock_fetch.return_value = mock_transcript

        result = self.extractor.get_transcript("dQw4w9WgXcQ")

        self.assertTrue(result["success"])
        self.assertEqual(
            result["text"],
            "This is a test transcript text This is a test transcript text",
        )
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["video_id"], "dQw4w9WgXcQ")

    @patch("youtube_transcript_api.YouTubeTranscriptApi.fetch")
    def test_get_transcript_disabled(self, mock_fetch):
        """Test transcript when disabled"""
        mock_fetch.side_effect = Exception("Transcripts are disabled")

        result = self.extractor.get_transcript("dQw4w9WgXcQ")

        self.assertFalse(result["success"])
        self.assertIn("disabled", result["error"].lower())

    @patch("youtube_transcript_api.YouTubeTranscriptApi.fetch")
    def test_get_transcript_unavailable(self, mock_fetch):
        """Test transcript when video unavailable"""
        mock_fetch.side_effect = Exception("Video is unavailable")

        result = self.extractor.get_transcript("dQw4w9WgXcQ")

        self.assertFalse(result["success"])
        self.assertIn("unavailable", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
