import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.sentinel import SentinelAgent
import asyncio

def main():
    agent = SentinelAgent()
    print("running scan...")
    candidates = agent.scan_for_updates()
    
    print(f"\nFound {len(candidates)} candidates:")
    for c in candidates:
        print(f"[{c['source_name']}] {c['title']}")
        print(f"   Date: {c['published']}")
        print("-" * 20)

if __name__ == "__main__":
    main()
