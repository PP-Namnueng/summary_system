"""
PDF document text extractor
"""
import io
from typing import Union
import fitz  # PyMuPDF


class PDFExtractor:
    """Extract text content from PDF documents"""

    def __init__(self, max_pages: int = 100):
        """
        Initialize PDF extractor
        
        Args:
            max_pages: Maximum number of pages to extract (default: 100)
        """
        self.max_pages = max_pages

    def extract_from_file(self, file_path: str) -> dict:
        """
        Extract text from a PDF file path
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            dict with extracted content
        """
        try:
            doc = fitz.open(file_path)
            return self._extract_from_document(doc, source=file_path)
        except Exception as e:
            return {
                "text": "",
                "error": f"Failed to open PDF: {str(e)}",
                "success": False,
            }

    def extract_from_bytes(self, pdf_bytes: bytes, filename: str = "uploaded.pdf") -> dict:
        """
        Extract text from PDF bytes (for file uploads)
        
        Args:
            pdf_bytes: PDF file content as bytes
            filename: Original filename
            
        Returns:
            dict with extracted content
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            return self._extract_from_document(doc, source=filename)
        except Exception as e:
            return {
                "text": "",
                "error": f"Failed to read PDF: {str(e)}",
                "success": False,
            }

    def _extract_from_document(self, doc: fitz.Document, source: str) -> dict:
        """
        Extract text from PyMuPDF document
        
        Args:
            doc: PyMuPDF document object
            source: Source identifier (filename or path)
            
        Returns:
            dict with extracted content
        """
        try:
            total_pages = len(doc)
            pages_to_extract = min(total_pages, self.max_pages)
            
            all_text = []
            
            for page_num in range(pages_to_extract):
                page = doc[page_num]
                
                # Extract text with better formatting
                text = page.get_text("text")
                
                if text.strip():
                    all_text.append(f"--- Page {page_num + 1} ---\n{text}")
            
            # Get metadata
            metadata = doc.metadata
            title = metadata.get("title", "") if metadata else ""
            author = metadata.get("author", "") if metadata else ""
            
            doc.close()
            
            full_text = "\n\n".join(all_text)
            
            if full_text.strip():
                return {
                    "text": full_text,
                    "title": title,
                    "author": author,
                    "total_pages": total_pages,
                    "extracted_pages": pages_to_extract,
                    "source": source,
                    "success": True,
                }
            else:
                return {
                    "text": "",
                    "error": "PDF contains no extractable text (might be scanned/image-based)",
                    "total_pages": total_pages,
                    "source": source,
                    "success": False,
                }
                
        except Exception as e:
            return {
                "text": "",
                "error": f"Error extracting text: {str(e)}",
                "source": source,
                "success": False,
            }

    def extract(self, source: Union[str, bytes], filename: str = None) -> dict:
        """
        Main extraction method - auto-detect source type
        
        Args:
            source: File path (str) or file content (bytes)
            filename: Original filename (required for bytes)
            
        Returns:
            dict with extracted content
        """
        if isinstance(source, bytes):
            return self.extract_from_bytes(source, filename or "uploaded.pdf")
        elif isinstance(source, str):
            return self.extract_from_file(source)
        else:
            return {
                "text": "",
                "error": "Invalid source type. Expected file path or bytes.",
                "success": False,
            }
