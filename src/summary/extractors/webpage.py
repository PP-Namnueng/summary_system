"""
Web page content extractor
"""
import requests
from typing import Optional
from urllib.parse import urlparse
import trafilatura
from bs4 import BeautifulSoup


class WebPageExtractor:
    """Extract main content from web pages"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "th,en;q=0.9",
        }

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")

    def _extract_with_trafilatura(self, html: str, url: str) -> dict:
        """Extract content using trafilatura (best for articles)"""
        try:
            # Extract main content
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=False,
                include_links=False,
                output_format="txt",
            )
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(html)
            
            title = ""
            if metadata:
                title = metadata.title or ""
            
            return {
                "text": text or "",
                "title": title,
                "method": "trafilatura",
            }
        except Exception:
            return {"text": "", "title": "", "method": "trafilatura"}

    def _extract_with_beautifulsoup(self, html: str) -> dict:
        """Fallback extraction using BeautifulSoup"""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove unwanted elements
            for element in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Try to find main content
            main_content = None
            for selector in ["article", "main", ".content", ".post", "#content", ".article"]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                body = soup.find("body")
                text = body.get_text(separator="\n", strip=True) if body else ""
            
            # Get title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # Clean up text
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)
            
            return {
                "text": text,
                "title": title,
                "method": "beautifulsoup",
            }
        except Exception:
            return {"text": "", "title": "", "method": "beautifulsoup"}

    def extract(self, url: str) -> dict:
        """
        Main extraction method
        
        Args:
            url: Web page URL
            
        Returns:
            dict with extracted content
        """
        if not self._is_valid_url(url):
            return {
                "text": "",
                "title": "",
                "error": "Invalid URL format",
                "success": False,
            }
        
        try:
            html = self._fetch_html(url)
            
            # Try trafilatura first (better for articles)
            result = self._extract_with_trafilatura(html, url)
            
            # Fallback to BeautifulSoup if trafilatura fails
            if not result["text"]:
                result = self._extract_with_beautifulsoup(html)
            
            if result["text"]:
                return {
                    "text": result["text"],
                    "title": result["title"],
                    "url": url,
                    "method": result["method"],
                    "success": True,
                }
            else:
                return {
                    "text": "",
                    "title": "",
                    "url": url,
                    "error": "Could not extract content from page",
                    "success": False,
                }
                
        except Exception as e:
            return {
                "text": "",
                "title": "",
                "url": url,
                "error": str(e),
                "success": False,
            }
