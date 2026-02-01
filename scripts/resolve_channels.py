import json
import re
import urllib.request
import os

SOURCES_PATH = r"c:\Users\PP\Desktop\Programming\summary\data\sources.json"

def get_channel_id(url):
    try:
        # Check if already correct
        if "feeds/videos.xml" in url:
            return None 
            
        # Add https if missing
        if not url.startswith("http"):
            url = "https://" + url
            
        print(f"Fetching {url}...")
        # Use a browser-like User Agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Pattern 1: <meta itemprop="channelId" content="UC..."
            match = re.search(r'itemprop="channelId" content="([a-zA-Z0-9_-]+)"', html)
            if match:
                return match.group(1)
            
            # Pattern 2: "channelId":"UC..."
            match = re.search(r'"channelId":"([a-zA-Z0-9_-]+)"', html)
            if match:
                return match.group(1)
            
            # Debug: Save HTML
            with open("debug_html.txt", "w", encoding="utf-8") as f:
                f.write(html)
            print("  -> Saved debug_html.txt")
                
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def main():
    if not os.path.exists(SOURCES_PATH):
        print("No sources file found.")
        return

    with open(SOURCES_PATH, 'r', encoding='utf-8') as f:
        sources = json.load(f)
    
    modified = False
    for src in sources:
        if src['type'] == 'youtube' and 'feeds/videos.xml' not in src['url']:
            print(f"Processing: {src['name']} ({src['url']})")
            cid = get_channel_id(src['url'])
            if cid:
                new_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
                print(f"  -> Fixed URL: {new_url}")
                src['url'] = new_url
                modified = True
            else:
                print("  -> Could not find Channel ID")

    if modified:
        with open(SOURCES_PATH, 'w', encoding='utf-8') as f:
            json.dump(sources, f, indent=4)
        print("✅ Successfully updated sources.json")
    else:
        print("No URL updates needed.")

if __name__ == "__main__":
    main()
