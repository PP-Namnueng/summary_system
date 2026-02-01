"""
Test Observer GitHub Trending
"""
import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from summary.agents.observer import ObserverAgent
from summary.library.github_provider import GitHubProvider

def test_manual_trending():
    print("Testing GitHubProvider directly...")
    provider = GitHubProvider()
    repos = provider.fetch_trending_repos()
    print(f"Fetched {len(repos)} repos.")
    if repos:
        print(f"First repo: {repos[0]['name']}")

def test_observer_integration():
    print("\nTesting ObserverAgent integration...")
    
    # Use a temp watchlist
    temp_watchlist = "tests/temp_watchlist.json"
    if os.path.exists(temp_watchlist):
        os.remove(temp_watchlist)
        
    agent = ObserverAgent(watchlist_path=temp_watchlist)
    
    # Add topic specific for Python
    agent.add_topic("github:python")
    print("Python topic added.")
    
    # Verify watchlist
    watchlist = agent.get_watchlist()
    print(f"Watchlist: {watchlist}")
    
    assert len(watchlist) == 1
    assert watchlist[0]['type'] == 'github_trending'
    assert watchlist[0]['language'] == 'python'
    assert watchlist[0]['topic'] == 'GitHub Trending: Python' # Check display name update
    
    # Run scan
    print("Running scan_topic for Python...")
    result = agent.scan_topic(watchlist[0])
    
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        top_news = result.get("top_news", [])
        print(f"Found {len(top_news)} updates.")
        for item in top_news:
             print(f"- {item['title']} ({item['url']})")
             
    # Cleanup
    if os.path.exists(temp_watchlist):
        os.remove(temp_watchlist)

if __name__ == "__main__":
    test_manual_trending()
    test_observer_integration()
