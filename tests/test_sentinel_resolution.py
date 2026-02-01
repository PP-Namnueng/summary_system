
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sentinel import SentinelAgent

class TestSentinelResolution(unittest.TestCase):
    def setUp(self):
        # Use a temporary file for sources
        self.agent = SentinelAgent(data_file="tests/temp_sources.json", output_dir="tests/temp_output")

    def tearDown(self):
        if os.path.exists("tests/temp_sources.json"):
            os.remove("tests/temp_sources.json")
        if os.path.exists("tests/temp_output"):
            import shutil
            shutil.rmtree("tests/temp_output")

    def test_non_youtube_url(self):
        url = "https://example.com/rss.xml"
        resolved = self.agent._resolve_youtube_rss(url)
        self.assertEqual(resolved, url)

    def test_existing_rss_url(self):
        url = "https://www.youtube.com/feeds/videos.xml?channel_id=UC12345"
        resolved = self.agent._resolve_youtube_rss(url)
        self.assertEqual(resolved, url)

    @patch('requests.get')
    def test_youtube_handle_resolution(self, mock_get):
        # Mock successful response with channelId
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><meta itemprop="channelId" content="UC_MOCKED_ID_123"></html>'
        mock_get.return_value = mock_response

        url = "https://www.youtube.com/@MockUser"
        resolved = self.agent._resolve_youtube_rss(url)
        
        expected = "https://www.youtube.com/feeds/videos.xml?channel_id=UC_MOCKED_ID_123"
        self.assertEqual(resolved, expected)

    @patch('requests.get')
    def test_youtube_channel_resolution_fallback_pattern(self, mock_get):
        # Mock successful response with JSON pattern
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html>"channelId":"UC_JSON_ID_456"</html>'
        mock_get.return_value = mock_response

        url = "https://www.youtube.com/c/SomeChannel"
        resolved = self.agent._resolve_youtube_rss(url)
        
        expected = "https://www.youtube.com/feeds/videos.xml?channel_id=UC_JSON_ID_456"
        self.assertEqual(resolved, expected)

if __name__ == '__main__':
    unittest.main()
