import json
import os
import datetime
import asyncio
from duckduckgo_search import DDGS
from summary.summarizer import OllamaSummarizer
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

    async def scan_topic_async(self, topic_data):
        """
        Async version of scan_topic.
        """
        # Run the synchronous scan_topic in a separate thread to not block the event loop
        return await asyncio.to_thread(self._scan_topic_internal, topic_data)

    def scan_topic(self, topic_data):
        """
        Legacy synchronous wrapper
        """
        return self._scan_topic_internal(topic_data)

    def _scan_topic_internal(self, topic_data):
        """
        Internal sync implementation of scanning logic
        """
        topic = topic_data['topic']
        source_type = topic_data.get('type', 'news')
        # print(f"DEBUG: Scanning topic: {topic} (Type: {source_type})") # Disabled to prevent WinError 233 in threads
        
        # --- Type: GitHub Trending ---
        if source_type == 'github_trending':
            try:
                provider = GitHubProvider()
                language = topic_data.get("language", None)
                repos = provider.fetch_trending_repos(language=language)
                
                if not repos:
                    return {"top_news": [], "error": "No repos found"}

                # Batch processing: summarize all 5 in one go
                top_5_repos = repos[:5]
                repo_descriptions = []
                for i, r in enumerate(top_5_repos):
                    desc = r.get('description', 'No description')
                    repo_descriptions.append(f"Repo {i+1}: Name='{r['name']}', Desc='{desc}'")

                combined_input = "\n".join(repo_descriptions)
                
                prompt = f"""
                Task: Summarize these 5 GitHub repositories in Thai.
                
                Input:
                {combined_input}
                
                Constraint: Return a JSON list of strings. Each string is a 3-line Thai summary for the corresponding repo.
                Example Output:
                [
                    "Summary for repo 1...",
                    "Summary for repo 2...",
                    ...
                ]
                
                Output JSON ONLY:"""

                try:
                    resp = self.summarizer._generate_response(prompt)
                    output_text = resp.get("summary", "").strip()
                    
                    # Clean markdown code blocks if present
                    if "```" in output_text:
                        import re
                        match = re.search(r"```(?:json)?(.*?)```", output_text, re.DOTALL)
                        if match:
                            output_text = match.group(1).strip()
                            
                    summaries = json.loads(output_text)
                    
                    # Ensure we have 5 items, fallback if mismatch
                    if not isinstance(summaries, list) or len(summaries) != len(top_5_repos):
                        summaries = [f"Summary gen failed. Original: {r.get('description')}" for r in top_5_repos]
                        
                except Exception as e:
                    print(f"Batch summary failed: {e}")
                    summaries = [r.get('description', '') for r in top_5_repos]

                # Assemble final result
                top_news = []
                for i, repo in enumerate(top_5_repos):
                    summary = summaries[i] if i < len(summaries) else repo.get('description', '')
                    top_news.append({
                        "title": f"📈 {repo['name']} ({repo['language']})",
                        "summary": f"{summary}\n(⭐ {repo['stars']} | 🍴 {repo['forks']})",
                        "url": repo['url'],
                        "date": datetime.datetime.now().strftime("%Y-%m-%d")
                    })
                    
                return {"top_news": top_news}

            except Exception as e:
                return {"top_news": [], "error": f"GitHub Fetch failed: {e}"}

        # --- Type: News (Default) ---
        results = []
        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.news(topic, region="wt-wt", safesearch="off", timelimit="w", max_results=15))
                for i, r in enumerate(search_results):
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
            resp_obj = self.summarizer._generate_response(prompt)
            
            if not resp_obj.get("success"):
                return {"top_news": [], "error": f"LLM Generation failed: {resp_obj.get('error')}"}
                
            response = resp_obj.get("summary", "")
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

