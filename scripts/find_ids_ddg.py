from duckduckgo_search import DDGS

queries = [
    "site:youtube.com/channel/ GratitudeDriven", 
    "site:youtube.com/channel/ LifeMeetsCode",
    "GratitudeDriven youtube channel id",
    "LifeMeetsCode youtube channel id"
]

print("Searching...")
try:
    with DDGS() as ddgs:
        for q in queries:
            print(f"\n--- Query: {q} ---")
            results = [r for r in ddgs.text(q, max_results=2)]
            for r in results:
                print(f"URL: {r['href']}")
                print(f"Snippet: {r['body']}")
except Exception as e:
    print(f"Error: {e}")
