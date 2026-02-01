"""
Test Research Agent functionality
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from summary.agents.research_agent import ResearchAgent


class TestResearchAgentInit(unittest.TestCase):
    """Test initialization of ResearchAgent"""

    @patch("agents.research_agent.ddg.AsyncDDGS")
    def test_init_default(self, mock_ddg):
        """Test initialization with default parameters"""
        agent = ResearchAgent()

        self.assertIsNotNone(agent)

    @patch("agents.research_agent.ddg.AsyncDDGS")
    def test_init_with_model(self, mock_ddg):
        """Test initialization with custom model"""
        agent = ResearchAgent(model_name="llama3.2")

        self.assertIsNotNone(agent)


class TestResearchAgentSearch(unittest.TestCase):
    """Test search functionality"""

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("asyncio.run")
    def test_search_basic(self, mock_run, mock_ddg):
        """Test basic search"""
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(
            return_value=[
                {
                    "title": "Test Result",
                    "href": "https://example.com",
                    "body": "Test content",
                }
            ]
        )
        mock_ddg.return_value = mock_ddg_instance

        agent = ResearchAgent()
        results = agent.search("AI and machine learning")

        self.assertIsInstance(results, list)

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("asyncio.run")
    def test_search_empty_query(self, mock_run, mock_ddg):
        """Test search with empty query"""
        agent = ResearchAgent()
        results = agent.search("")

        # Should handle empty query gracefully
        self.assertIsInstance(results, list)

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("asyncio.run")
    def test_search_thai_query(self, mock_run, mock_ddg):
        """Test search with Thai query"""
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(
            return_value=[
                {
                    "title": "ผลการค้นหา",
                    "href": "https://example.com",
                    "body": "เนื้อหาภาษาไทย",
                }
            ]
        )
        mock_ddg.return_value = mock_ddg_instance

        agent = ResearchAgent()
        results = agent.search("ปัญญาประดิษฐ์")

        self.assertIsInstance(results, list)


class TestResearchAgentResearch(unittest.TestCase):
    """Test research functionality"""

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("summarizer.ollama_client.OllamaSummarizer")
    @patch("asyncio.run")
    def test_research_topic(self, mock_run, mock_summarizer, mock_ddg):
        """Test researching a topic"""
        # Mock search results
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(
            return_value=[
                {
                    "title": "AI Research",
                    "href": "https://example.com/ai",
                    "body": "Content about AI",
                }
            ]
        )
        mock_ddg.return_value = mock_ddg_instance

        # Mock summarizer
        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = {
            "success": True,
            "summary": "# AI Research Summary\n\nThis is a summary",
        }
        mock_summarizer.return_value = mock_summarizer_instance

        agent = ResearchAgent()
        result = agent.research("Artificial Intelligence", num_results=3)

        self.assertIn("report", result)

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("summarizer.ollama_client.OllamaSummarizer")
    @patch("asyncio.run")
    def test_research_with_multiple_sources(self, mock_run, mock_summarizer, mock_ddg):
        """Test research with multiple sources"""
        # Mock search results
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(
            return_value=[
                {
                    "title": "Source 1",
                    "href": "https://example.com/1",
                    "body": "Content 1",
                },
                {
                    "title": "Source 2",
                    "href": "https://example.com/2",
                    "body": "Content 2",
                },
                {
                    "title": "Source 3",
                    "href": "https://example.com/3",
                    "body": "Content 3",
                },
            ]
        )
        mock_ddg.return_value = mock_ddg_instance

        # Mock summarizer
        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = {
            "success": True,
            "summary": "Combined summary",
        }
        mock_summarizer.return_value = mock_summarizer_instance

        agent = ResearchAgent()
        result = agent.research("Test topic", num_results=3)

        self.assertIn("report", result)
        self.assertIn("sources", result)

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("summarizer.ollama_client.OllamaSummarizer")
    @patch("asyncio.run")
    def test_research_error_handling(self, mock_run, mock_summarizer, mock_ddg):
        """Test error handling in research"""
        # Mock search to return empty results
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(return_value=[])
        mock_ddg.return_value = mock_ddg_instance

        agent = ResearchAgent()
        result = agent.research("Test topic")

        # Should handle gracefully
        self.assertIn("report", result)


class TestResearchAgentDeepResearch(unittest.TestCase):
    """Test deep research functionality"""

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("summarizer.ollama_client.OllamaSummarizer")
    @patch("asyncio.run")
    def test_deep_research(self, mock_run, mock_summarizer, mock_ddg):
        """Test deep research with multiple rounds"""
        # Mock search results
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(
            return_value=[
                {
                    "title": "Deep Result",
                    "href": "https://example.com",
                    "body": "Deep content",
                }
            ]
        )
        mock_ddg.return_value = mock_ddg_instance

        # Mock summarizer
        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = {
            "success": True,
            "summary": "Deep research summary",
        }
        mock_summarizer.return_value = mock_summarizer_instance

        agent = ResearchAgent()
        result = agent.deep_research("Complex topic")

        self.assertIn("report", result)


class TestResearchAgentContext(unittest.TestCase):
    """Test context and query handling"""

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("asyncio.run")
    def test_search_with_context(self, mock_run, mock_ddg):
        """Test search with provided context"""
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(
            return_value=[
                {
                    "title": "Contextual Result",
                    "href": "https://example.com",
                    "body": "Contextual content",
                }
            ]
        )
        mock_ddg.return_value = mock_ddg_instance

        agent = ResearchAgent()
        results = agent.search(
            query="specific term", context=["previous context", "related info"]
        )

        self.assertIsInstance(results, list)

    @patch("agents.research_agent.ddg.AsyncDDGS")
    @patch("asyncio.run")
    def test_refine_query(self, mock_run, mock_ddg):
        """Test query refinement"""
        mock_ddg_instance = MagicMock()
        mock_ddg_instance.atext.return_value = AsyncMock(
            return_value=[
                {
                    "title": "Refined Result",
                    "href": "https://example.com",
                    "body": "Refined content",
                }
            ]
        )
        mock_ddg.return_value = mock_ddg_instance

        agent = ResearchAgent()
        results = agent.search("AI ML")

        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
