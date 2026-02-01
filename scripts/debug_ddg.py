from duckduckgo_search import DDGS
import json

def test_query(query):
    print(f"--- Testing Query: '{query}' ---")
    backends = ['api', 'html', 'lite']
    
    for backend in backends:
        print(f"Trying backend: {backend}...")
        try:
            results = []
            with DDGS() as ddgs:
                # Use same params as agent
                gen = ddgs.text(query, max_results=5, backend=backend)
                for r in gen:
                    results.append(r)
            
            print(f"  Success! Found {len(results)} results.")
            if results:
                print(f"  Top result: {results[0].get('title')} - {results[0].get('href')}")
                return # Stop if successful
            else:
                print("  backend returned 0 results.")
                
        except Exception as e:
            print(f"  Error with {backend}: {e}")

if __name__ == "__main__":
    test_query("Context Engineer")
    test_query("Context Engineering AI")
    test_query("Python")
