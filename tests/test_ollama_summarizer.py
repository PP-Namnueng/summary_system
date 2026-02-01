"""
Test Ollama Summarizer functionality
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, Mock
from typing import Generator

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from summary.summarizer.ollama_client import OllamaSummarizer


class TestOllamaSummarizerInit(unittest.TestCase):
    """Test initialization of OllamaSummarizer"""

    @patch("summarizer.ollama_client.ollama.Client")
    def test_init_with_model(self, mock_ollama_client):
        """Test initialization with specific model"""
        mock_client_instance = MagicMock()
        mock_ollama_client.return_value = mock_client_instance

        summarizer = OllamaSummarizer(model="llama3.2")

        self.assertEqual(summarizer.model, "llama3.2")
        self.assertIsNotNone(summarizer.client)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_init_without_model(self, mock_ollama_client):
        """Test initialization without model (auto-detect)"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_model = MagicMock()
        mock_model.model = "llama3.2:latest"
        mock_response.models = [mock_model]
        mock_client_instance.list.return_value = mock_response
        mock_ollama_client.return_value = mock_client_instance

        summarizer = OllamaSummarizer()

        self.assertIsNotNone(summarizer.model)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_init_with_custom_timeout(self, mock_ollama_client):
        """Test initialization with custom timeout"""
        mock_client_instance = MagicMock()
        mock_ollama_client.return_value = mock_client_instance

        summarizer = OllamaSummarizer(timeout=300)

        self.assertEqual(summarizer.timeout, 300)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_init_with_context_window(self, mock_ollama_client):
        """Test initialization with custom context window"""
        mock_client_instance = MagicMock()
        mock_ollama_client.return_value = mock_client_instance

        summarizer = OllamaSummarizer(num_ctx=16384)

        self.assertEqual(summarizer.num_ctx, 16384)


class TestOllamaSummarizerConnection(unittest.TestCase):
    """Test Ollama connection and model detection"""

    @patch("summarizer.ollama_client.ollama.Client")
    def test_check_connection_success(self, mock_ollama_client_class):
        """Test successful connection check"""
        mock_client_instance = MagicMock()
        mock_client_instance.list.return_value = {}
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.check_connection()

        self.assertTrue(result)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_check_connection_failure(self, mock_ollama_client_class):
        """Test connection check when Ollama is not running"""
        mock_client_instance = MagicMock()
        mock_client_instance.list.side_effect = Exception("Connection refused")
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.check_connection()

        self.assertFalse(result)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_get_available_models(self, mock_ollama_client_class):
        """Test getting list of available models"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_model1 = MagicMock()
        mock_model1.model = "llama3.2:latest"
        mock_model2 = MagicMock()
        mock_model2.model = "mistral:latest"
        mock_response.models = [mock_model1, mock_model2]
        mock_client_instance.list.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        models = summarizer.get_available_models()

        self.assertEqual(len(models), 2)
        self.assertIn("llama3.2:latest", models)
        self.assertIn("mistral:latest", models)


class TestOllamaSummarizerSummarize(unittest.TestCase):
    """Test summarization methods"""

    @patch("summarizer.ollama_client.ollama.Client")
    def test_summarize_empty_content(self, mock_ollama_client_class):
        """Test summarization with empty content"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.summarize("", language="th")

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "No content provided")

    @patch("summarizer.ollama_client.ollama.Client")
    def test_summarize_none_content(self, mock_ollama_client_class):
        """Test summarization with None content"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.summarize(None, language="th")

        self.assertFalse(result["success"])

    @patch("summarizer.ollama_client.ollama.Client")
    def test_summarize_thai_content(self, mock_ollama_client_class):
        """Test summarization in Thai"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "นี่คือสรุปภาษาไทย"
        mock_client_instance.generate.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.summarize("This is test content", language="th")

        self.assertTrue(result["success"])
        self.assertIn("summary", result)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_summarize_english_content(self, mock_ollama_client_class):
        """Test summarization in English"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "This is the summary"
        mock_client_instance.generate.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.summarize("This is test content", language="en")

        self.assertTrue(result["success"])
        self.assertIn("summary", result)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_summarize_with_template(self, mock_ollama_client_class):
        """Test summarization with different template"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Executive summary content"
        mock_client_instance.generate.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.summarize("Content", language="en", template="executive")

        self.assertTrue(result["success"])

    @patch("summarizer.ollama_client.ollama.Client")
    def test_summarize_with_content_type(self, mock_ollama_client_class):
        """Test summarization with different content types"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "PDF summary content"
        mock_client_instance.generate.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.summarize(
            "PDF content", language="en", content_type="PDF Document"
        )

        self.assertTrue(result["success"])


class TestOllamaSummarizerStreaming(unittest.TestCase):
    """Test streaming functionality"""

    @patch("summarizer.ollama_client.ollama.Client")
    def test_stream_summary(self, mock_ollama_client_class):
        """Test streaming summary"""
        mock_client_instance = MagicMock()
        # Mock streaming response
        mock_stream = [
            MagicMock(response="Hello"),
            MagicMock(response=" world"),
            MagicMock(response="!"),
        ]
        mock_client_instance.generate.return_value = mock_stream
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.summarize("Test content", stream=True)

        # Streaming returns a generator
        self.assertTrue(callable(result) or isinstance(result, Generator))


class TestOllamaSummarizerChat(unittest.TestCase):
    """Test chat functionality"""

    @patch("summarizer.ollama_client.ollama.Client")
    def test_chat_with_message(self, mock_ollama_client_class):
        """Test chat with a message"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "This is a response"
        mock_client_instance.generate.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.chat("Hello, how are you?")

        self.assertTrue(result["success"])
        self.assertIn("response", result)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_chat_with_empty_message(self, mock_ollama_client_class):
        """Test chat with empty message"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        result = summarizer.chat("")

        self.assertFalse(result["success"])

    @patch("summarizer.ollama_client.ollama.Client")
    def test_chat_with_history(self, mock_ollama_client_class):
        """Test chat with conversation history"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Based on our conversation..."
        mock_client_instance.generate.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        history = [
            {"role": "user", "content": "What is AI?"},
            {"role": "assistant", "content": "AI stands for Artificial Intelligence"},
        ]
        result = summarizer.chat("Tell me more", history=history)

        self.assertTrue(result["success"])

    @patch("summarizer.ollama_client.ollama.Client")
    def test_chat_with_context(self, mock_ollama_client_class):
        """Test chat with document context"""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "Based on the document context..."
        mock_client_instance.generate.return_value = mock_response
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        context = "This is a document about machine learning."
        result = summarizer.chat("Explain machine learning", context=context)

        self.assertTrue(result["success"])


class TestOllamaSummarizerLongContent(unittest.TestCase):
    """Test handling of long content"""

    @patch("summarizer.ollama_client.ollama.Client")
    def test_chunk_content(self, mock_ollama_client_class):
        """Test content chunking"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()

        # Short content - no chunking
        short_content = "Short content"
        chunks = summarizer._chunk_content(short_content)
        self.assertEqual(len(chunks), 1)

        # Long content - should be chunked
        long_content = "Paragraph 1\n\n" + "Paragraph 2\n\n" * 50
        chunks = summarizer._chunk_content(long_content, max_chars=1000)
        self.assertGreater(len(chunks), 1)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_summarize_long_content(self, mock_ollama_client_class):
        """Test summarization of long content"""
        mock_client_instance = MagicMock()
        # Mock response for chunk summarization
        mock_chunk_response = MagicMock()
        mock_chunk_response.response = "Chunk summary"
        # Mock response for final summary
        mock_final_response = MagicMock()
        mock_final_response.response = "Final combined summary"
        mock_client_instance.generate.side_effect = [mock_chunk_response] * 3 + [
            mock_final_response
        ]
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        long_content = "Paragraph 1\n\n" + "Paragraph 2\n\n" * 50
        result = summarizer.summarize_long_content(long_content, language="en")

        # Success depends on implementation
        # Should handle long content properly
        self.assertIn("summary", result)


class TestOllamaSummarizerPrompts(unittest.TestCase):
    """Test prompt generation"""

    @patch("summarizer.ollama_client.ollama.Client")
    def test_thai_summary_prompt(self, mock_ollama_client_class):
        """Test Thai summary prompt generation"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        prompt = summarizer._get_thai_summary_prompt("Test content", "test")

        self.assertIn("ภาษาไทย", prompt)
        self.assertIn("Test content", prompt)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_english_summary_prompt(self, mock_ollama_client_class):
        """Test English summary prompt generation"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        prompt = summarizer._get_english_summary_prompt("Test content", "test")

        self.assertIn("Analyst Mode", prompt)
        self.assertIn("Test content", prompt)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_executive_prompt(self, mock_ollama_client_class):
        """Test executive summary prompt"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        prompt = summarizer._get_executive_prompt("Content", "test", "en")

        self.assertIn("EXECUTIVE SUMMARY", prompt)
        self.assertIn("Business Impact", prompt)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_technical_prompt(self, mock_ollama_client_class):
        """Test technical deep-dive prompt"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        prompt = summarizer._get_technical_prompt("Content", "test", "en")

        self.assertIn("TECHNICAL DEEP-DIVE", prompt)
        self.assertIn("Architecture", prompt)

    @patch("summarizer.ollama_client.ollama.Client")
    def test_eli5_prompt(self, mock_ollama_client_class):
        """Test ELI5 prompt"""
        mock_client_instance = MagicMock()
        mock_ollama_client_class.return_value = mock_client_instance

        summarizer = OllamaSummarizer()
        prompt = summarizer._get_eli5_prompt("Content", "test", "en")

        self.assertIn("Explain Like I'm 5", prompt)
        self.assertIn("NO jargon", prompt)


if __name__ == "__main__":
    unittest.main()
