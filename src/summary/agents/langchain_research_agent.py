"""
LangChain Research Agent with Tools
Uses direct tool calls for research (simpler, more reliable).
"""
from typing import Optional, List, Generator
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun
import requests


class ResearchTools:
    """Collection of research tools."""
    
    @staticmethod
    def web_search(query: str) -> str:
        """DuckDuckGo web search."""
        try:
            search = DuckDuckGoSearchRun()
            return search.run(query)
        except Exception as e:
            return f"Search error: {e}"
    
    @staticmethod
    def arxiv_search(query: str) -> str:
        """Search arXiv for academic papers."""
        try:
            import arxiv
            
            search = arxiv.Search(
                query=query,
                max_results=5,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            results = []
            for paper in search.results():
                results.append(f"""
**{paper.title}**
- Authors: {', '.join([a.name for a in paper.authors[:3]])}
- Published: {paper.published.strftime('%Y-%m-%d')}
- Summary: {paper.summary[:300]}...
- URL: {paper.pdf_url}
""")
            
            if not results:
                return "No papers found."
            
            return "\n---\n".join(results)
            
        except ImportError:
            return "arXiv library not installed."
        except Exception as e:
            return f"arXiv error: {e}"
    
    @staticmethod
    def hackernews_search(query: str) -> str:
        """Search HackerNews for tech discussions."""
        try:
            url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=5"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return "Error connecting to HackerNews"
            
            data = response.json()
            hits = data.get("hits", [])
            
            if not hits:
                return "No HackerNews discussions found."
            
            results = []
            for hit in hits:
                title = hit.get("title", "Untitled")
                hn_url = hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)
                
                results.append(f"- **{title}** ({points} points, {comments} comments)\n  {hn_url}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"HackerNews error: {e}"


class LangChainResearchAgent:
    """
    Multi-tool research agent.
    Searches web, arXiv, and HackerNews, then synthesizes results.
    """
    
    def __init__(self, model: str = "llama3.1", num_ctx: int = 8192):
        """Initialize research agent."""
        self.model_name = model
        self.num_ctx = num_ctx
        self.llm = ChatOllama(
            model=model,
            base_url="http://localhost:11434",
            timeout=300.0,
            num_ctx=num_ctx
        )
    
    def set_model(self, model: str, num_ctx: int = None):
        """Change model."""
        self.model_name = model
        if num_ctx:
            self.num_ctx = num_ctx
        self.llm = ChatOllama(
            model=model,
            base_url="http://localhost:11434",
            timeout=300.0,
            num_ctx=self.num_ctx
        )
    
    def research(self, topic: str, max_sources: int = 5) -> dict:
        """Research a topic using multiple tools."""
        return self.research_stream(topic)
    
    def research_stream(self, topic: str) -> dict:
        """
        Research with step tracking.
        """
        steps = []
        all_results = {}
        
        # Step 1: Web search
        try:
            web_result = ResearchTools.web_search(topic)
            steps.append({"tool": "web_search", "input": topic, "output": web_result[:500]})
            all_results["web"] = web_result
        except Exception as e:
            steps.append({"tool": "web_search", "input": topic, "output": f"Error: {e}"})
        
        # Step 2: arXiv search (for technical topics)
        try:
            arxiv_result = ResearchTools.arxiv_search(topic)
            steps.append({"tool": "arxiv_search", "input": topic, "output": arxiv_result[:500]})
            all_results["arxiv"] = arxiv_result
        except Exception as e:
            steps.append({"tool": "arxiv_search", "input": topic, "output": f"Error: {e}"})
        
        # Step 3: HackerNews search
        try:
            hn_result = ResearchTools.hackernews_search(topic)
            steps.append({"tool": "hackernews_search", "input": topic, "output": hn_result[:500]})
            all_results["hackernews"] = hn_result
        except Exception as e:
            steps.append({"tool": "hackernews_search", "input": topic, "output": f"Error: {e}"})
        
        # Step 4: Synthesize with LLM
        try:
            combined = "\n\n".join([
                f"## Web Search Results\n{all_results.get('web', 'No results')}",
                f"## Academic Papers (arXiv)\n{all_results.get('arxiv', 'No results')}",
                f"## Tech Discussions (HackerNews)\n{all_results.get('hackernews', 'No results')}"
            ])
            
            prompt = f"""You are a research analyst. Based on the following search results, create a comprehensive research report on: **{topic}**

{combined}

Create a well-organized report that:
1. Summarizes key findings from all sources
2. Identifies main themes and trends
3. Highlights important facts and data
4. Notes any academic/scientific perspectives
5. Mentions industry discussions and opinions
6. Provides a balanced conclusion

Format with clear headers and bullet points."""

            response = self.llm.invoke(prompt)
            report = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "success": True,
                "report": report,
                "steps": steps,
                "topic": topic
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "steps": steps,
                "topic": topic
            }


def get_research_agent(model: str = "llama3.1", num_ctx: int = 8192) -> LangChainResearchAgent:
    """Factory function to get research agent."""
    return LangChainResearchAgent(model=model, num_ctx=num_ctx)
