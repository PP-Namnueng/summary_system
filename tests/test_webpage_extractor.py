"""
Test Web Page Extractor functionality
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, Mock
from bs4 import BeautifulSoup

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extractors.webpage import WebPageExtractor


class TestWebPageExtractor(unittest.TestCase):
    """Test cases for WebPageExtractor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = WebPageExtractor()

    @patch("requests.get")
    def test_extract_successful(self, mock_get):
        """Test successful extraction from web page"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Test Article</title>
            </head>
            <body>
                <article>
                    <h1>Main Heading</h1>
                    <p>This is the first paragraph of the article.</p>
                    <p>This is the second paragraph.</p>
                </article>
            </body>
        </html>
        """
        mock_response.url = "https://example.com/article"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com/article")

        self.assertTrue(result["success"])
        self.assertIn("Main Heading", result["text"])
        self.assertEqual(result["url"], "https://example.com/article")

    @patch("requests.get")
    def test_extract_with_trafilatura(self, mock_get):
        """Test extraction using trafilatura as fallback"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Trafilatura test content</p></body></html>"
        mock_response.url = "https://example.com/test"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com/test")

        self.assertTrue(result["success"])
        self.assertIn("test content", result["text"])

    @patch("requests.get")
    def test_extract_url_not_found(self, mock_get):
        """Test handling of 404 error"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com/notfound")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("requests.get")
    def test_extract_timeout(self, mock_get):
        """Test handling of timeout errors"""
        mock_get.side_effect = Exception("Connection timeout")

        result = self.extractor.extract("https://example.com/slow")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("requests.get")
    def test_extract_invalid_url(self, mock_get):
        """Test handling of invalid URL"""
        result = self.extractor.extract("not-a-valid-url")

        self.assertFalse(result["success"])


class TestWebPageExtractorContent(unittest.TestCase):
    """Test content extraction from different page types"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = WebPageExtractor()

    @patch("requests.get")
    def test_extract_from_news_article(self, mock_get):
        """Test extraction from news article page"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>Breaking News</title></head>
            <body>
                <article>
                    <h1>Major Event Happened Today</h1>
                    <p class="lead">This is a breaking news story about an important event.</p>
                    <p>Additional details about the event.</p>
                </article>
            </body>
        </html>
        """
        mock_response.url = "https://news.example.com/breaking"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://news.example.com/breaking")

        self.assertTrue(result["success"])
        self.assertIn("Major Event Happened", result["text"])

    @patch("requests.get")
    def test_extract_from_blog_post(self, mock_get):
        """Test extraction from blog post"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><title>My Blog Post</title></head>
            <body>
                <div class="blog-post">
                    <h1>Understanding AI</h1>
                    <p>Artificial Intelligence is transforming our world.</p>
                    <p>Here's what you need to know.</p>
                </div>
            </body>
        </html>
        """
        mock_response.url = "https://blog.example.com/ai"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://blog.example.com/ai")

        self.assertTrue(result["success"])
        self.assertIn("Understanding AI", result["text"])

    @patch("requests.get")
    def test_extract_empty_page(self, mock_get):
        """Test extraction from empty page"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"
        mock_response.url = "https://example.com/empty"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com/empty")

        self.assertTrue(result["success"])
        # Empty or minimal text
        self.assertTrue(len(result["text"]) < 100)

    @patch("requests.get")
    def test_extract_page_with_unicode(self, mock_get):
        """Test extraction from page with Unicode content"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <h1>International Content</h1>
                <p>English, 中文, 日本語, العربية, עברית</p>
            </body>
        </html>
        """
        mock_response.url = "https://example.com/international"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com/international")

        self.assertTrue(result["success"])
        self.assertIn("中文", result["text"])


class TestWebPageExtractorHeaders(unittest.TestCase):
    """Test header extraction and metadata"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = WebPageExtractor()

    @patch("requests.get")
    def test_extract_page_title(self, mock_get):
        """Test extraction of page title"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <title>Page Title Here</title>
            </head>
            <body>
                <h1>Article Title</h1>
                <p>Content here</p>
            </body>
        </html>
        """
        mock_response.url = "https://example.com"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com")

        self.assertTrue(result["success"])
        # Should contain title information

    @patch("requests.get")
    def test_extract_meta_description(self, mock_get):
        """Test extraction of meta description"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head>
                <meta name="description" content="This is the page description">
            </head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """
        mock_response.url = "https://example.com"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com")

        self.assertTrue(result["success"])


class TestWebPageExtractorEdgeCases(unittest.TestCase):
    """Test edge cases for WebPageExtractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = WebPageExtractor()

    @patch("requests.get")
    def test_redirect_handling(self, mock_get):
        """Test URL redirects"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://final-destination.com"
        mock_response.history = [MagicMock(url="https://original.com")]
        mock_response.text = "<html><body><h1>Redirected Content</h1></body></html>"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://original.com")

        self.assertTrue(result["success"])
        self.assertEqual(result["url"], "https://final-destination.com")

    @patch("requests.get")
    def test_very_long_page(self, mock_get):
        """Test extraction from very long page"""
        long_content = "<p>" + "Lorem ipsum dolor sit amet. " * 1000 + "</p>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            f"<html><body><h1>Long Page</h1>{long_content}</body></html>"
        )
        mock_response.url = "https://example.com/long"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com/long")

        self.assertTrue(result["success"])
        self.assertGreater(len(result["text"]), 10000)

    @patch("requests.get")
    def test_page_with_scripts_and_styles(self, mock_get):
        """Test filtering of scripts and styles"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <script>var x = 'javascript code';</script>
                <style>body { color: red; }</style>
                <h1>Main Content</h1>
                <p>This should be extracted.</p>
            </body>
        </html>
        """
        mock_response.url = "https://example.com"
        mock_get.return_value = mock_response

        result = self.extractor.extract("https://example.com")

        self.assertTrue(result["success"])
        self.assertIn("Main Content", result["text"])
        self.assertIn("This should be extracted", result["text"])


if __name__ == "__main__":
    unittest.main()
