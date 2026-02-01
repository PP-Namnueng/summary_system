import sys
sys.path.insert(0, 'c:/Users/PP/Desktop/Programming/summary')

from agents.research_agent import ResearchAgent
from unittest.mock import MagicMock

def test_research_flow():
    print("=== Testing Research Flow ===")
    
    # Create agent with mock summarizer to avoid LLM call
    mock_summarizer = MagicMock()
    mock_summarizer._stream_response = MagicMock(return_value=iter(["Test report chunk 1", "Test report chunk 2"]))
    
    agent = ResearchAgent(summarizer=mock_summarizer)
    
    topic = "Context Engineer"
    print(f"Topic: {topic}")
    
    # Test search first
    print("\n--- Testing search_web ---")
    results = agent.search_web(topic, max_results=3)
    print(f"Search returned {len(results)} results")
    for r in results:
        print(f"  - {r.get('title', 'No title')[:50]}")
    
    if not results:
        print("ERROR: No search results!")
        return
    
    # Test full research flow
    print("\n--- Testing research_topic generator ---")
    gen = agent.research_topic(topic, max_sources=3, language="en")
    
    for update in gen:
        if isinstance(update, str):
            print(f"[STATUS] {update}")
        elif isinstance(update, dict):
            print(f"[{update.get('type', 'unknown')}] {str(update)[:100]}...")

if __name__ == "__main__":
    test_research_flow()
