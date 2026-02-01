"""
Fetch Trending Script
Orchestrates fetching GitHub trending repos and saving them to the library.
"""
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.github_provider import GitHubProvider
from library.document_store import DocumentStore

def create_markdown_report(repos: list, date_str: str) -> str:
    """Create a markdown report from the repos list."""
    md = f"# GitHub Trending - {date_str}\n\n"
    md += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    if not repos:
        md += "No trending repositories found or error fetching data.\n"
        return md
        
    for i, repo in enumerate(repos, 1):
        md += f"## {i}. [{repo['name']}]({repo['url']})\n"
        md += f"**Language:** {repo['language']} | **Stars:** {repo['stars']} | **Forks:** {repo['forks']}\n\n"
        md += f"{repo['description']}\n\n"
        md += "---\n\n"
        
    return md

def main():
    print("Initializing GitHub Provider...")
    provider = GitHubProvider()
    
    print("Fetching trending repositories...")
    repos = provider.fetch_trending_repos()
    
    if not repos:
        print("No repositories fetched. Exiting.")
        return

    print(f"Fetched {len(repos)} repositories.")
    
    # Create Markdown content
    date_str = datetime.now().strftime('%Y-%m-%d')
    markdown_content = create_markdown_report(repos, date_str)
    
    # Save to file
    filename = f"GitHub_Trending_{date_str}.md"
    temp_path = os.path.join(os.path.dirname(__file__), filename)
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
        
    print(f"Report generated at: {temp_path}")
    
    # Add to Document Store
    print("Adding to Document Store...")
    doc_store = DocumentStore()
    
    try:
        # We start with copy_file=True to let DocumentStore manage it, 
        # but since we just created it in scripts/, we can let it copy to library/documents/
        # and then we can remove the temp file if we want, or keep it.
        # Let's keep it simple: let DocumentStore copy it.
        
        metadata = doc_store.add_document(
            file_path=temp_path,
            title=f"GitHub Trending {date_str}",
            author="GitHub System",
            copy_file=True
        )
        print(f"Successfully added to library: {metadata['doc_id']}")
        
        # Cleanup temp file
        os.remove(temp_path)
        print("Cleaned up temporary file.")
        
    except Exception as e:
        print(f"Error adding to document store: {e}")

if __name__ == "__main__":
    main()
