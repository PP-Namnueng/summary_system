import json
import feedparser
import os

DATA_FILE = r"c:\Users\PP\Desktop\Programming\summary\data\sources.json"

def main():
    if not os.path.exists(DATA_FILE):
        print("No sources.json found.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        sources = json.load(f)

    print(f"Checking {len(sources)} sources...\n")

    for src in sources:
        print(f"--- {src['name']} ---")
        print(f"URL: {src['url']}")
        try:
            feed = feedparser.parse(src['url'])
            if not feed.entries:
                print("  [!] No entries found in feed.")
            else:
                for i, entry in enumerate(feed.entries[:5]):
                    print(f"  {i+1}. {entry.get('title', 'No Title')}")
                    print(f"     Published: {entry.get('published', 'No Date')}")
                    print(f"     Link: {entry.get('link', '')}")
        except Exception as e:
           print(f"  [Error] {e}")
        print("")

if __name__ == "__main__":
    main()
