"""
Test PDF Extractor functionality
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
import io

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from summary.extractors.pdf import PDFExtractor


class TestPDFExtractor(unittest.TestCase):
    """Test cases for PDFExtractor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = PDFExtractor()

    @patch("fitz.open")
    def test_extract_text_from_file(self, mock_fitz_open):
        """Test extracting text from PDF file path"""
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample PDF text content"
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        result = self.extractor.extract("test.pdf")

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "Sample PDF text content")
        self.assertEqual(result["source"], "test.pdf")

    @patch("fitz.open")
    def test_extract_text_from_bytes(self, mock_fitz_open):
        """Test extracting text from PDF bytes"""
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDF from bytes"
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        pdf_bytes = b"fake pdf content"
        result = self.extractor.extract(pdf_bytes, "test.pdf")

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "PDF from bytes")

    @patch("fitz.open")
    def test_extract_multiple_pages(self, mock_fitz_open):
        """Test extracting text from multi-page PDF"""
        # Mock PDF with multiple pages
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 content"
        mock_page3 = MagicMock()
        mock_page3.get_text.return_value = "Page 3 content"

        mock_doc.__iter__.return_value = [mock_page1, mock_page2, mock_page3]
        mock_doc.__len__.return_value = 3
        mock_fitz_open.return_value = mock_doc

        result = self.extractor.extract("test.pdf")

        self.assertTrue(result["success"])
        self.assertEqual(
            result["text"], "Page 1 content\n\nPage 2 content\n\nPage 3 content"
        )
        self.assertEqual(result["page_count"], 3)

    @patch("fitz.open")
    def test_extract_empty_pdf(self, mock_fitz_open):
        """Test extracting text from empty PDF"""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 0
        mock_fitz_open.return_value = mock_doc

        result = self.extractor.extract("test.pdf")

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "")

    @patch("fitz.open")
    def test_extract_pdf_with_unicode(self, mock_fitz_open):
        """Test extracting text with Unicode characters"""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Hello 世界 🌍"
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        result = self.extractor.extract("test.pdf")

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "Hello 世界 🌍")
        self.assertEqual(result["char_count"], 9)

    @patch("fitz.open")
    def test_extract_pdf_metadata(self, mock_fitz_open):
        """Test metadata extraction from PDF"""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text"
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_doc.name = "TestDocument.pdf"
        mock_fitz_open.return_value = mock_doc

        result = self.extractor.extract("test.pdf")

        self.assertTrue(result["success"])
        self.assertIn("metadata", result)


class TestPDFExtractorErrorHandling(unittest.TestCase):
    """Test error handling in PDFExtractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = PDFExtractor()

    @patch("fitz.open")
    def test_file_not_found(self, mock_fitz_open):
        """Test handling of non-existent file"""
        mock_fitz_open.side_effect = FileNotFoundError("File not found")

        result = self.extractor.extract("nonexistent.pdf")

        self.assertFalse(result["success"])
        self.assertIn("file not found", result["error"].lower())

    @patch("fitz.open")
    def test_corrupted_pdf(self, mock_fitz_open):
        """Test handling of corrupted PDF"""
        mock_fitz_open.side_effect = Exception("PDF is corrupted")

        result = self.extractor.extract("corrupted.pdf")

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_invalid_input_type(self):
        """Test handling of invalid input type"""
        result = self.extractor.extract(12345)  # Invalid type

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_empty_filename(self):
        """Test handling of empty filename"""
        result = self.extractor.extract("")

        self.assertFalse(result["success"])


class TestPDFExtractorEdgeCases(unittest.TestCase):
    """Test edge cases for PDFExtractor"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = PDFExtractor()

    @patch("fitz.open")
    def test_very_long_text(self, mock_fitz_open):
        """Test extracting very long text content"""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # Generate long text
        long_text = "Lorem ipsum " * 10000
        mock_page.get_text.return_value = long_text
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        result = self.extractor.extract("long.pdf")

        self.assertTrue(result["success"])
        self.assertGreater(len(result["text"]), 100000)
        self.assertEqual(result["char_count"], len(long_text))

    @patch("fitz.open")
    def test_special_characters(self, mock_fitz_open):
        """Test extracting text with special characters"""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        special_text = "© 2024 • Special @#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        mock_page.get_text.return_value = special_text
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        result = self.extractor.extract("special.pdf")

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], special_text)


if __name__ == "__main__":
    unittest.main()
