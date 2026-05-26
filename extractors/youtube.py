"""
YouTube video transcript extractor with multiple fallback methods.

Extraction priority:
1. youtube-transcript-api (lightweight, fast)
2. Direct HTTP scrape of YouTube page + transcript URL (no dependencies)
3. yt-dlp with browser cookies (heavy but robust)
"""
import re
import json
import urllib.request
import urllib.parse
import http.cookiejar
from pathlib import Path
from typing import Optional


class YouTubeExtractor:
    """Extract transcripts from YouTube videos"""
    
    # Default cookie file locations to search
    COOKIE_FILENAMES = ["cookies.txt", "youtube_cookies.txt"]
    
    # Browser-like headers to avoid bot detection
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    def __init__(self, cookies_path: str = None):
        """
        Initialize YouTubeExtractor
        
        Args:
            cookies_path: Optional explicit path to cookies.txt file.
                          If not provided, auto-detects from project root.
        """
        self.cookies_path = cookies_path or self._find_cookies()
        if self.cookies_path:
            print(f"[cookies] YouTube cookies loaded from: {self.cookies_path}")
    
    def _find_cookies(self) -> Optional[str]:
        """Auto-detect cookies.txt file from project root"""
        current = Path(__file__).resolve().parent
        for _ in range(5):
            for name in self.COOKIE_FILENAMES:
                cookie_file = current / name
                if cookie_file.exists():
                    return str(cookie_file)
            current = current.parent
        return None

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
        if not url:
            return None

        parsed = urllib.parse.urlparse(url.strip())
        host = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.strip("/")

        if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
            if path == "watch":
                video_id = urllib.parse.parse_qs(parsed.query).get("v", [None])[0]
                if video_id and re.fullmatch(r"[a-zA-Z0-9_-]{11}", video_id):
                    return video_id
            for prefix in ("embed/", "v/", "shorts/", "live/"):
                if path.startswith(prefix):
                    candidate = path[len(prefix):].split("/")[0]
                    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", candidate):
                        return candidate

        if host == "youtu.be":
            candidate = path.split("/")[0]
            if re.fullmatch(r"[a-zA-Z0-9_-]{11}", candidate):
                return candidate

        patterns = [
            r"(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})",
            r"(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
            r"(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})",
            r"(?:youtu\.be\/)([a-zA-Z0-9_-]{11})",
            r"(?:youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    # ─── Method 1: youtube-transcript-api ───────────────────────────────

    def _get_transcript_ytapi(self, video_id: str, languages: list[str]) -> dict:
        """Try fetching transcript using youtube-transcript-api"""
        from youtube_transcript_api import YouTubeTranscriptApi

        def fetch_with_current_api():
            api = YouTubeTranscriptApi(http_client=self._build_ytt_session())
            transcript_list = api.list(video_id)
            try:
                transcript = transcript_list.find_transcript(languages)
            except Exception:
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except Exception:
                    raise RuntimeError(f"No transcript available in languages: {languages}")

            transcript_data = transcript.fetch()
            return {
                "text": self._transcript_entries_to_text(transcript_data),
                "language": getattr(transcript_data, "language_code", transcript.language_code),
                "video_id": video_id,
                "success": True,
            }

        def fetch_with_legacy_api():
            attempts = []
            if self.cookies_path:
                attempts.append({"cookies": self.cookies_path})
            attempts.append({})

            last_error = None
            for kwargs in attempts:
                try:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, **kwargs)
                
                    try:
                        transcript = transcript_list.find_transcript(languages)
                    except Exception:
                        try:
                            transcript = transcript_list.find_generated_transcript(languages)
                        except Exception:
                            raise RuntimeError(f"No transcript available in languages: {languages}")

                    return {
                        "text": self._transcript_entries_to_text(transcript.fetch()),
                        "language": transcript.language_code,
                        "video_id": video_id,
                        "success": True,
                    }
                except Exception as e:
                    last_error = e
                    continue
            raise last_error or RuntimeError("youtube-transcript-api failed")

        if hasattr(YouTubeTranscriptApi, "list_transcripts"):
            return fetch_with_legacy_api()
        return fetch_with_current_api()

    def _build_ytt_session(self):
        """Build a requests session for youtube-transcript-api 1.x."""
        try:
            import requests
        except ImportError:
            return None

        session = requests.Session()
        session.headers.update(self.HEADERS)

        if self.cookies_path:
            try:
                cookie_jar = http.cookiejar.MozillaCookieJar(self.cookies_path)
                cookie_jar.load(ignore_discard=True, ignore_expires=True)
                session.cookies.update(cookie_jar)
            except Exception as e:
                print(f"[warn] Could not load YouTube cookies for transcript API: {e}")

        return session

    @staticmethod
    def _transcript_entries_to_text(transcript_data) -> str:
        """Convert transcript-api return types from both old and new versions."""
        if hasattr(transcript_data, "to_raw_data"):
            transcript_data = transcript_data.to_raw_data()

        texts = []
        for entry in transcript_data:
            if isinstance(entry, dict):
                text = entry.get("text", "")
            else:
                text = getattr(entry, "text", "")
            text = str(text).strip()
            if text:
                texts.append(text)
        return " ".join(texts)

    # ─── Method 2: Direct HTTP scrape (no extra dependencies) ───────────

    def _get_transcript_direct(self, video_id: str, languages: list[str]) -> dict:
        """
        Fetch transcript by directly scraping YouTube page HTML.
        
        This method:
        1. Fetches the YouTube video page with browser-like headers
        2. Extracts caption track URLs from the embedded JSON
        3. Downloads and parses the transcript XML directly
        
        No cookies or authentication needed for most public videos.
        """
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Fetch the video page with browser-like headers
        req = urllib.request.Request(video_url, headers=self.HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8")
        
        # Extract captions JSON from ytInitialPlayerResponse
        captions_json = self._extract_captions_from_html(html)
        if not captions_json:
            raise RuntimeError("No caption data found in video page")
        
        # Find the best matching caption track
        caption_tracks = captions_json.get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
        if not caption_tracks:
            raise RuntimeError("No caption tracks available for this video")
        
        # Find track matching preferred language
        selected_track = None
        detected_lang = None
        
        for lang in languages:
            for track in caption_tracks:
                track_lang = track.get("languageCode", "")
                if track_lang == lang or track_lang.startswith(lang):
                    selected_track = track
                    detected_lang = track_lang
                    break
            if selected_track:
                break
        
        # Fallback to first available track
        if not selected_track:
            selected_track = caption_tracks[0]
            detected_lang = selected_track.get("languageCode", "unknown")
        
        # Fetch the transcript XML
        caption_url = selected_track.get("baseUrl")
        if not caption_url:
            raise RuntimeError("No caption URL found")
        
        # Request JSON3 format transcript
        if "fmt=" not in caption_url:
            caption_url += "&fmt=json3"
        
        req = urllib.request.Request(caption_url, headers=self.HEADERS)
        with urllib.request.urlopen(req, timeout=15) as response:
            raw_data = response.read().decode("utf-8")
        
        if not raw_data or len(raw_data) < 10:
            raise RuntimeError("Empty transcript response from YouTube")
        
        # Try parsing as JSON3 first, then XML
        full_text = self._parse_transcript_data(raw_data)
        
        if not full_text:
            raise RuntimeError("Could not parse transcript data")
        
        return {
            "text": full_text,
            "language": detected_lang,
            "video_id": video_id,
            "success": True,
        }
    
    def _extract_captions_from_html(self, html: str) -> Optional[dict]:
        """Extract captions JSON from YouTube page HTML"""
        player_response = self._extract_json_object_after_marker(html, "ytInitialPlayerResponse")
        if player_response:
            if "captions" in player_response:
                return player_response["captions"]
            if "playerCaptionsTracklistRenderer" in player_response:
                return player_response

        # Try ytInitialPlayerResponse
        patterns = [
            (r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;', re.DOTALL),
            (r'"captions"\s*:\s*({.+?})\s*,\s*"', re.DOTALL),
        ]

        for pattern, flags in patterns:
            match = re.search(pattern, html, flags)
            if match:
                try:
                    data = json.loads(match.group(1))
                    # If full player response, extract captions section
                    if "captions" in data:
                        return data["captions"]
                    if "playerCaptionsTracklistRenderer" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        
        # Fallback: try to find captionTracks directly
        match = re.search(r'"captionTracks"\s*:\s*(\[.+?\])', html, re.DOTALL)
        if match:
            try:
                tracks = json.loads(match.group(1))
                return {"playerCaptionsTracklistRenderer": {"captionTracks": tracks}}
            except json.JSONDecodeError:
                pass
        
        return None

    @staticmethod
    def _extract_json_object_after_marker(html: str, marker: str) -> Optional[dict]:
        marker_index = html.find(marker)
        if marker_index == -1:
            return None

        start = html.find("{", marker_index)
        if start == -1:
            return None

        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(html)):
            char = html[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html[start:index + 1])
                    except json.JSONDecodeError:
                        return None

        return None
    
    def _parse_vtt(self, raw_data: str) -> str:
        """Parse VTT subtitle format into plain text"""
        lines = raw_data.splitlines()
        texts = []
        for line in lines:
            line = line.strip()
            # Skip headers, timestamps, and empty lines
            if not line:
                continue
            if line.startswith("WEBVTT"):
                continue
            if re.match(r'^\d+$', line):  # cue number
                continue
            if re.match(r'[\d:.]+ --> [\d:.]+', line):  # timestamp
                continue
            if line.startswith("NOTE") or line.startswith("STYLE") or line.startswith("REGION"):
                continue
            # Remove inline tags like <00:00:00.000>, <c>, </c>
            line = re.sub(r'<[^>]+>', '', line)
            line = line.strip()
            if line:
                texts.append(line)
        
        # Deduplicate consecutive duplicate lines (common in auto-captions)
        deduped = []
        for text in texts:
            if not deduped or deduped[-1] != text:
                deduped.append(text)
        
        return " ".join(deduped)

    def _parse_transcript_data(self, raw_data: str) -> str:
        """Parse transcript data from JSON3, XML, or VTT format"""
        # Try JSON3 format first
        try:
            data = json.loads(raw_data)
            events = data.get("events", [])
            texts = []
            for event in events:
                segs = event.get("segs", [])
                for seg in segs:
                    text = seg.get("utf8", "").strip()
                    if text and text != "\n":
                        texts.append(text)
            if texts:
                return " ".join(texts)
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Try VTT format
        if "WEBVTT" in raw_data:
            result = self._parse_vtt(raw_data)
            if result:
                return result
        
        # Try XML format
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(raw_data)
            texts = []
            for text_elem in root.iter("text"):
                if text_elem.text:
                    # Unescape HTML entities
                    text = text_elem.text.strip()
                    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                    text = text.replace("&#39;", "'").replace("&quot;", '"')
                    if text:
                        texts.append(text)
            if texts:
                return " ".join(texts)
        except Exception:
            pass
        
        return ""

    # ─── Method 3: yt-dlp fallback ──────────────────────────────────────

    def _get_transcript_ytdlp(self, video_id: str, languages: list[str]) -> dict:
        """Fallback: fetch transcript using yt-dlp with cookies file"""
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("yt-dlp is not installed")
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Only use cookies file — skip browser cookie attempts (DPAPI issues on Windows)
        cookie_attempts = []
        if self.cookies_path:
            cookie_attempts.append(self.cookies_path)
        cookie_attempts.append(None)  # anonymous fallback
        
        import tempfile
        import os
        
        last_error = None
        for cookie_file in cookie_attempts:
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    ydl_opts = {
                        "skip_download": True,
                        "writesubtitles": True,
                        "writeautomaticsub": True,
                        "subtitleslangs": languages,
                        "subtitlesformat": "vtt",  # vtt is more stable than json3
                        "quiet": True,
                        "no_warnings": True,
                        "outtmpl": os.path.join(temp_dir, "video.%(ext)s"),
                    }
                    
                    if cookie_file:
                        ydl_opts["cookiefile"] = cookie_file
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        ydl.process_info(info)
                    
                    # Find the downloaded subtitle file
                    sub_path = None
                    detected_lang = None
                    
                    for lang in languages:
                        expected_path = os.path.join(temp_dir, f"video.{lang}.vtt")
                        if os.path.exists(expected_path):
                            sub_path = expected_path
                            detected_lang = lang
                            break
                    
                    if not sub_path:
                        # Fallback: find any subtitle file downloaded
                        for file in os.listdir(temp_dir):
                            if any(file.endswith(ext) for ext in [".vtt", ".json3", ".srv3", ".ttml", ".srt"]):
                                sub_path = os.path.join(temp_dir, file)
                                # Extract lang from video.{lang}.{ext}
                                parts = file.replace("video.", "").rsplit(".", 1)
                                detected_lang = parts[0] if parts else "auto"
                                break
                                
                    if not sub_path:
                        raise RuntimeError("Subtitle download failed or no subtitles in requested languages")
                    
                    with open(sub_path, "r", encoding="utf-8") as f:
                        raw_data = f.read()

                    full_text = self._parse_transcript_data(raw_data)
                    
                    return {
                        "text": full_text,
                        "language": detected_lang or "auto",
                        "video_id": video_id,
                        "success": True,
                    }
                    
            except Exception as e:
                last_error = e
                continue
        
        raise last_error or RuntimeError("yt-dlp failed to fetch transcript")

    # ─── Main orchestrator ──────────────────────────────────────────────

    def get_transcript(self, video_id: str, languages: list[str] = None) -> dict:
        """
        Get transcript for a YouTube video.
        Tries 3 methods in order:
          1. youtube-transcript-api
          2. Direct HTTP scrape (no cookies needed)
          3. yt-dlp with cookies file
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: ['th', 'en'])
            
        Returns:
            dict with 'text', 'language', and 'video_id'
        """
        if languages is None:
            languages = ["th", "en"]
        
        errors = []
        
        # Method 1: youtube-transcript-api
        try:
            return self._get_transcript_ytapi(video_id, languages)
        except Exception as e:
            errors.append(f"youtube-transcript-api: {e}")
            print(f"[warn] Method 1 failed: {e}")
        
        # Method 2: Direct HTTP scrape
        try:
            print("[retry] Trying direct HTTP scrape...")
            return self._get_transcript_direct(video_id, languages)
        except Exception as e:
            errors.append(f"direct-scrape: {e}")
            print(f"[warn] Method 2 failed: {e}")
        
        # Method 3: yt-dlp fallback
        try:
            print("[retry] Trying yt-dlp fallback...")
            return self._get_transcript_ytdlp(video_id, languages)
        except Exception as e:
            errors.append(f"yt-dlp: {e}")
            print(f"[error] Method 3 failed: {e}")
        
        # All methods failed — return friendly error
        first_error = errors[0] if errors else "Unknown error"
        if "TranscriptsDisabled" in first_error or "disabled" in first_error.lower():
            error_msg = "Transcripts are disabled for this video"
        elif "VideoUnavailable" in first_error or "unavailable" in first_error.lower():
            error_msg = "Video is unavailable"
        elif "No transcript found" in first_error or "No caption" in first_error:
            error_msg = "No transcript found in requested languages"
        else:
            error_msg = "Could not fetch transcript. All methods failed."
        
        return {
            "text": "",
            "error": error_msg,
            "video_id": video_id,
            "success": False,
        }

    def extract(self, url: str) -> dict:
        """
        Main extraction method
        
        Args:
            url: YouTube video URL
            
        Returns:
            dict with extracted content
        """
        video_id = self.extract_video_id(url)
        
        if not video_id:
            return {
                "text": "",
                "error": "Invalid YouTube URL",
                "success": False,
            }
        
        return self.get_transcript(video_id)
