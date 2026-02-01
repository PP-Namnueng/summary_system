"""
Test configuration and utilities
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test directory
TEST_DIR = Path(__file__).parent
TEMP_DIR = TEST_DIR / "temp"


def setup_test_environment():
    """Set up test environment"""
    # Create temp directory if it doesn't exist
    TEMP_DIR.mkdir(exist_ok=True)

    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["OLLAMA_HOST"] = "http://localhost:11434"


def cleanup_test_environment():
    """Clean up test environment"""
    # Remove temp files
    if TEMP_DIR.exists():
        import shutil

        shutil.rmtree(TEMP_DIR, ignore_errors=True)


def get_test_file_path(filename):
    """Get path to test data file"""
    return TEST_DIR / "fixtures" / filename


def create_temp_file(content, filename):
    """Create a temporary test file"""
    TEMP_DIR.mkdir(exist_ok=True)
    temp_file = TEMP_DIR / filename
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)
    return str(temp_file)


def create_mock_pdf_content(text):
    """Create mock PDF content for testing"""
    return {"text": text, "page_count": 1, "char_count": len(text), "success": True}


def create_mock_youtube_transcript(text):
    """Create mock YouTube transcript for testing"""
    return {
        "text": text,
        "language": "en",
        "video_id": "test_video_id",
        "success": True,
    }


def create_mock_webpage_content(title, body):
    """Create mock webpage content for testing"""
    return {"text": f"{title}\n\n{body}", "url": "https://example.com", "success": True}
