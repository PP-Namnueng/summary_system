from agents.research_agent import ResearchAgent
from unittest.mock import MagicMock

def test_search():
    print("Initializing Agent with Mock Summarizer...")
    mock_summarizer = MagicMock()
    agent = ResearchAgent(summarizer=mock_summarizer)
    
    query = "Python"
    print(f"Testing search for '{query}'...")
    
    # Max results 3
    results = agent.search_web(query, max_results=3)
    
    print(f"Found {len(results)} results.")
    for r in results:
        print(f"- {r.get('title')} ({r.get('href')})")

if __name__ == "__main__":
    test_search()
