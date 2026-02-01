import json
import os
import datetime
from duckduckgo_search import DDGS
from summarizer.ollama_client import OllamaSummarizer
from library.github_provider import GitHubProvider

class ObserverAgent:
    def __init__(self, watchlist_path="data/watchlist.json", model_name="llama3.1"):
        self.watchlist_path = watchlist_path
        self.model_name = model_name
        self.summarizer = OllamaSummarizer(model=model_name)
        self.watchlist = self._load_watchlist()

    def _load_watchlist(self):
        if not os.path.exists(self.watchlist_path):
            return []
        try:
            with open(self.watchlist_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading watchlist: {e}")
            return []

    def _save_watchlist(self):
        os.makedirs(os.path.dirname(self.watchlist_path), exist_ok=True)
        with open(self.watchlist_path, 'w', encoding='utf-8') as f:
            json.dump(self.watchlist, f, indent=4, ensure_ascii=False)

    def get_watchlist(self):
        return self.watchlist

    def add_topic(self, topic, source_type="news"):
        # Auto-detect GitHub request
        extra_metadata = {}
        if topic.lower().startswith("github:"):
            source_type = "github_trending"
            parts = topic.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                lang_part = parts[1].strip()
                extra_metadata["language"] = lang_part
                # Update display topic to be nicer
                topic = f"GitHub Trending: {lang_part.capitalize()}"

        for item in self.watchlist:
            if item['topic'].lower() == topic.lower():
                return False  # Already exists
        
        entry = {
            "topic": topic,
            "type": source_type,
            "last_checked": "Never",
            "last_status": "Pending"
        }
        entry.update(extra_metadata)
        self.watchlist.append(entry)
        self._save_watchlist()
        return True

    def remove_topic(self, topic):
        initial_len = len(self.watchlist)
        self.watchlist = [t for t in self.watchlist if t['topic'] != topic]
        if len(self.watchlist) < initial_len:
            self._save_watchlist()
            return True
        return False

    def scan_topic(self, topic_data):
        """
        Scans a topic for recent news and returns the Top 5 curated stories.
        Returns a dict with 'top_news': list of dicts {title, summary, url, date}.
        """
        topic = topic_data['topic']
        source_type = topic_data.get('type', 'news')
        print(f"DEBUG: Scanning topic: {topic} (Type: {source_type})")
        
        # --- Type: GitHub Trending ---
        if source_type == 'github_trending':
            try:
                provider = GitHubProvider()
                # Get language from metadata if available
                language = topic_data.get("language", None)
                repos = provider.fetch_trending_repos(language=language)
                
                # Convert to news format
                top_news = []
                for repo in repos[:5]: # Top 5
                    original_desc = repo.get('description', 'No description')
                    
                    # Translate/Summarize to Thai
                    prompt = f"""
                    Context: A software tool named "{repo['name']}".
                    Description: "{original_desc}"
                    
                    Task: Explain what this tool does in Thai.
                    Constraint 1: Output MUST be in Thai language only.
                    Constraint 2: summary must be approximately 3 lines.
                    """
                    
                    try:
                        resp = self.summarizer._generate_response(prompt)
                        thai_desc = resp.get("summary", "").strip()
                        
                        # Fallback if empty
                        if not thai_desc:
                            thai_desc = f"(Auto-translation failed: {original_desc})"
                    except Exception as e:
                        thai_desc = f"{original_desc} (Error: {e})"

                    top_news.append({
                        "title": f"📈 {repo['name']} ({repo['language']})",
                        "summary": f"{thai_desc}\n(⭐ {repo['stars']} | 🍴 {repo['forks']})",
                        "url": repo['url'],
                        "date": datetime.datetime.now().strftime("%Y-%m-%d")
                    })
                return {"top_news": top_news}
            except Exception as e:
                return {"top_news": [], "error": f"GitHub Fetch failed: {e}"}

        # --- Type: News (Default) ---
        # 1. Broad News Scan (Last 7 days to ensure coverage)
        results = []
        try:
            with DDGS() as ddgs:
                # Get more results (15) to allow filtration
                search_results = list(ddgs.news(topic, region="wt-wt", safesearch="off", timelimit="w", max_results=15))
                # Map results to a temporary ID for the LLM to reference
                for i, r in enumerate(search_results):
                    # We pass the URL in the snippets so the LLM can grab it (or we map it back by index if unsafe)
                    # Safest is to ask LLM to return the index or just copy the URL.
                    # Let's give it an ID.
                    results.append(f"ID: {i} | Date: {r['date']} | Title: {r['title']} | Snippet: {r['body']} | Link: {r['url']}")
        except Exception as e:
            print(f"Error scanning topic {topic}: {e}")
            return {"top_news": [], "error": f"Search failed: {e}"}

        if not results:
             return {"top_news": [], "error": "No recent news found."}

        news_text = "\n\n".join(results)

        # 2. Curate Top 5 with LLM
        prompt = f"""
        You are a News Editor.
        Topic: "{topic}"
        
        Raw News Items (with IDs and Links):
        {news_text}

        Task:
        1. Select the Top 5 MOST IMPORTANT news items from the list above.
        2. If duplicate stories appear, select the best one and ignore the others.
        3. Summarize each item in Thai (Language: Thai ONLY).
        4. CRITICAL: Each summary must be exactly 3 lines long.
        5. YOU MUST PRESERVE THE CORRECT LINK (URL) for each item.

        Output JSON ONLY:
        {{
            "top_news": [
                {{
                    "title": "<Headline in Thai>",
                    "summary": "<3-line summary in Thai>",
                    "url": "<EXACT URL from source>",
                    "date": "<original date>"
                }},
                ...
            ]
        }}
        """
        
        try:
            # Use internal _generate_response method which returns a dict
            resp_obj = self.summarizer._generate_response(prompt)
            
            if not resp_obj.get("success"):
                return {"top_news": [], "error": f"LLM Generation failed: {resp_obj.get('error')}"}
                
            response = resp_obj.get("summary", "")
            # Clean up response to ensure valid JSON (sometimes LLMs add markdown code blocks)
            response = response.strip()
            if "```" in response:
                import re
                match = re.search(r"```(?:json)?(.*?)```", response, re.DOTALL)
                if match:
                    response = match.group(1).strip()
            
            digest = json.loads(response)
            return digest
        except Exception as e:
            print(f"Error curating news for {topic}: {e}")
            return {"top_news": [], "error": f"Curation failed: {e}"}

    def update_topic_status(self, topic, status):
        for item in self.watchlist:
            if item['topic'] == topic:
                item['last_checked'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                item['last_status'] = status
                break
        self._save_watchlist()
