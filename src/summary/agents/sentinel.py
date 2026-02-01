import json
import os
import feedparser
import datetime
from summary.agents.observer import ObserverAgent
from summary.generators.podcast_generator import PodcastGenerator
from summary.summarizer.ollama_client import OllamaSummarizer
import re
import requests
import asyncio

class SentinelAgent:
    def __init__(self, data_file="data/sources.json", output_dir="sentinel_outputs"):
        self.data_file = data_file
        self.output_dir = output_dir
        self.sources = self._load_sources()
        
        # Initialize dependencies
        # We can reuse OllamaSummarizer configurations if passed, but for now defaults
        self.summarizer = OllamaSummarizer()
        self.podcaster = PodcastGenerator(summarizer=self.summarizer)
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _load_sources(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_sources(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.sources, f, indent=4, ensure_ascii=False)

    def _resolve_youtube_rss(self, url):
        """
        Attempts to convert a YouTube URL (Handle, Channel, User) to an RSS feed URL.
        Returns the original URL if not a YouTube link or if resolution fails.
        """
        # 1. If already an RSS, return as is
        if "feeds/videos.xml" in url:
            return url
            
        # 2. Check if it's a YouTube URL
        if not any(x in url.lower() for x in ['youtube.com', 'youtu.be']):
            return url
            
        print(f"Resolving YouTube URL: {url}")
        
        try:
            # 3. Add https if missing
            if not url.startswith("http"):
                url = "https://" + url
                
            # 4. Fetch the page to find channelId
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            # Use specific cookies if needed, but usually public pages work
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Search for channelId in meta tags or JSON config
                # Pattern A: <meta itemprop="channelId" content="...">
                match_id = re.search(r'itemprop="channelId" content="([a-zA-Z0-9_-]+)"', html)
                
                # Pattern B: "channelId":"..."
                if not match_id:
                     match_id = re.search(r'"channelId":"([a-zA-Z0-9_-]+)"', html)
                     
                if match_id:
                    cid = match_id.group(1)
                    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
                    print(f"  -> Resolved to: {rss_url}")
                    return rss_url
                    
            print("  -> Could not resolve Channel ID. Using original.")
            
        except Exception as e:
            print(f"  -> Error resolving URL: {e}")
            
        return url

    def add_source(self, name, url, source_type="rss"):
        # Auto-resolve YouTube URLs
        if source_type == "youtube":
            url = self._resolve_youtube_rss(url)
            
        self.sources.append({
            "name": name,
            "url": url,
            "type": source_type,
            "last_checked": None,
            "seen_ids": []
        })
        self._save_sources()

    def remove_source(self, url):
        self.sources = [s for s in self.sources if s['url'] != url]
        self._save_sources()

    def update_source(self, original_url, new_name, new_url, new_type):
        """Updates an existing source's details."""
        for src in self.sources:
            if src['url'] == original_url:
                src['name'] = new_name
                src['url'] = new_url
                src['type'] = new_type
                break
        self._save_sources()

    def process_feed(self, source):
        """
        Fetches feed, identifies NEW items, and yields them for processing.
        """
        print(f"Checking source: {source['name']} ({source['url']})")
        
        # Parse RSS/Atom
        feed = feedparser.parse(source['url'])
        
        new_items = []
        seen_ids = set(source.get('seen_ids', []))
        
        # Check entries (assuming standard RSS/Atom structure)
        # Check entries (assuming standard RSS/Atom structure)
        # Scan ALL entries in the feed (usually 10-15) for new content
        for entry in feed.entries:
            # Use 'id' if available, else 'link' as unique identifier
            uid = getattr(entry, 'id', getattr(entry, 'link', None))
            
            if uid and uid not in seen_ids:
                new_items.append(entry)
                seen_ids.add(uid)
        
        # Update source state immediately (or after success? Let's say we saw them)
        source['seen_ids'] = list(seen_ids)[-50:] # Keep last 50 IDs
        source['last_checked'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_sources()
        
        return new_items

    def scan_for_updates(self):
        """
        Checks all sources for new items but DOES NOT process them yet.
        Returns a list of candidate items {source, title, link, uid, summary}.
        """
        candidates = []
        for source in self.sources:
            print(f"Scanning {source['name']}...")
            try:
                feed = feedparser.parse(source['url'])
                seen_ids = set(source.get('seen_ids', []))
                
                # Check all entries
                for entry in feed.entries:
                    uid = getattr(entry, 'id', getattr(entry, 'link', None))
                    
                    if uid and uid not in seen_ids:
                        candidates.append({
                            "source_name": source['name'],
                            "source_url": source['url'], # ID to find source back
                            "source_category": source.get('category', 'news'), # Default to news
                            "title": entry.get('title', 'Untitled'),
                            "link": entry.get('link', '#'),
                            "summary": entry.get('summary', entry.get('description', '')),
                            "uid": uid,
                            "published": entry.get('published', '')
                        })
            except Exception as e:
                print(f"Error scanning {source['name']}: {e}")
                
        return candidates

    def mark_as_seen(self, source_url, uid):
        """Marks an ID as seen for a specific source to prevent re-scanning."""
        for src in self.sources:
            if src['url'] == source_url:
                if 'seen_ids' not in src: src['seen_ids'] = []
                if uid not in src['seen_ids']:
                    src['seen_ids'].append(uid)
                    # Keep last 50
                    if len(src['seen_ids']) > 50:
                        src['seen_ids'] = src['seen_ids'][-50:]
                src['last_checked'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_sources()
                break

    async def process_item(self, item, vault_path=None):
        """
        Processes a SINGLE item: Summarize -> Podcast -> Save -> Mark Seen
        Yields status updates dict.
        """
        try:
            yield {"type": "log", "message": f"▶️ Starting: **{item['title']}**"}
            
            # 1. Summarize
            summary_prompt = f"""
            Source: {item['source_name']}
            Title: {item['title']}
            Content: {item['summary']}
            
            Task: Summarize this update into a concise, informative paragraph suitable for a casual reader.
            """
            summary_resp = self.summarizer._generate_response(summary_prompt)
            summary_text = summary_resp.get("summary", item['summary'])
            
            # 2. Generate Podcast
            yield {"type": "log", "message": f"   🎙️ Generating Audio for '{item['title'][:20]}...'"}
            script, err = self.podcaster.generate_script(summary_text, style="news")
            audio_path = None
            
            if script:
                safe_title = "".join([c for c in item['title'] if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')[:50]
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_filename = f"{timestamp}_{safe_title}.mp3"
                
                # Determine output path
                if vault_path and os.path.isdir(vault_path):
                    attach_dir = os.path.join(vault_path, "Attachments", "SentinelAudio")
                    if not os.path.exists(attach_dir):
                        os.makedirs(attach_dir)
                    audio_path = os.path.join(attach_dir, audio_filename)
                else:
                    audio_path = os.path.join(self.output_dir, audio_filename)
                
                # generate_audio is synchronous
                success, audio_err = self.podcaster.generate_audio(script, audio_path)
                if not success:
                    yield {"type": "log", "message": f"   ❌ Audio Error: {audio_err}"}
                    audio_path = None
            else:
                 yield {"type": "log", "message": f"   ❌ Script Error: {err}"}

            # 3. Yield Result Item
            yield {
                "type": "item",
                "title": item['title'],
                "summary": summary_text,
                "link": item['link'],
                "source": item['source_name'],
                "audio_path": audio_path,
                "date": datetime.datetime.now().strftime("%H:%M")
            }
            
            # 4. Mark as Seen (Success)
            self.mark_as_seen(item['source_url'], item['uid'])
            
        except Exception as e:
            yield {"type": "log", "message": f"❌ Error processing {item['title']}: {e}"}
