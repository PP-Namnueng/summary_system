from duckduckgo_search import DDGS

def test_simple_search():
    print("Testing simple DDG search...")
    queries = ["Context Engineer", "Python programming", "AI news"]
    
    for query in queries:
        print(f"\n--- Query: '{query}' ---")
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, max_results=3)
                result_list = list(results)
                print(f"Found {len(result_list)} results")
                for r in result_list[:2]:
                    print(f"  - {r.get('title', 'No title')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_search()
