import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from summary.agents.observer import ObserverAgent

def test_observer():
    print("Testing ObserverAgent (News Digest Mode)...")
    
    # Initialize
    agent = ObserverAgent(model_name="llama3.1")
    
    test_topic = "OpenAI News"
    print(f"\n1. Scanning '{test_topic}' for Top 5 News...")
    
    # Mock data to simulate watchlist item
    topic_data = {"topic": test_topic}
    
    digest = agent.scan_topic(topic_data)
    print(f"Digest Result Keys: {digest.keys()}")
    
    if "top_news" in digest:
        news_list = digest['top_news']
        print(f"✅ Found {len(news_list)} news items.")
        for i, news in enumerate(news_list):
            print(f"  {i+1}. {news.get('title')} ({news.get('date')})")
            print(f"     URL: {news.get('url')}")
            assert 'url' in news, "News item missing URL"
    else:
        print(f"❌ Failed: {digest.get('error')}")

if __name__ == "__main__":
    test_observer()
