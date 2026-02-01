from duckduckgo_search import DDGS
import json

def search():
    try:
        results = DDGS().text("youtube video OOO_x3Oh2nE channel id", max_results=5)
        for r in results:
            print(f"Title: {r['title']}")
            print(f"URL: {r['href']}")
            print(f"Body: {r['body']}")
            print("-" * 20)
            
        # Also try searching for the channel name directly again
        print("\n--- Channel Search ---")
        results = DDGS().text("Life Meets Code youtube channel id", max_results=3)
        for r in results:
            print(f"C-URL: {r['href']}")
            print(f"C-Body: {r['body']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search()
