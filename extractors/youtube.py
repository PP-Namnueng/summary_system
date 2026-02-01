"""
YouTube video transcript extractor
"""
import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeExtractor:
    """Extract transcripts from YouTube videos"""
    
    def __init__(self):
        self.api = YouTubeTranscriptApi()

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
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

    def get_transcript(self, video_id: str, languages: list[str] = None) -> dict:
        """
        Get transcript for a YouTube video
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: ['th', 'en'])
            
        Returns:
            dict with 'text', 'language', and 'video_id'
        """
        if languages is None:
            languages = ["th", "en"]
        
        try:
            # Fetch transcript using new API (instance method)
            transcript = self.api.fetch(video_id)
            
            # Get language info
            detected_lang = transcript.language_code if hasattr(transcript, 'language_code') else "auto"
            
            # Combine transcript text from snippets
            if hasattr(transcript, 'snippets'):
                full_text = " ".join([s.text for s in transcript.snippets])
            else:
                # Fallback for different response format
                full_text = " ".join([entry.text if hasattr(entry, 'text') else entry["text"] for entry in transcript])
            
            return {
                "text": full_text,
                "language": detected_lang,
                "video_id": video_id,
                "success": True,
            }
            
        except Exception as e:
            error_msg = str(e)
            if "disabled" in error_msg.lower():
                error_msg = "Transcripts are disabled for this video"
            elif "unavailable" in error_msg.lower():
                error_msg = "Video is unavailable"
            
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
