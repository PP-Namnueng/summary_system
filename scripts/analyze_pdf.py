import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.pdf_processor import PDFProcessor

def analyze_pdf(file_path):
    print(f"🔍 Analyzing: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    processor = PDFProcessor()
    
    try:
        # Extract Text
        print("1️⃣  Extracting text...")
        extraction = processor.extract_text(file_path)
        if not extraction.get("success"):
            print(f"❌ Extraction failed: {extraction.get('error')}")
            return
            
        full_text = extraction["full_text"]
        print(f"   - Pages: {extraction['page_count']}")
        print(f"   - Characters: {len(full_text):,}")
        
        # Detect Chapters (Using NEW strict logic)
        print("2️⃣  Detecting chapters...")
        chapters = processor.detect_chapters(full_text)
        print(f"   - Chapters found: {len(chapters)}")
        if chapters:
            print("   - First 5 Chapters detected:")
            for ch in chapters[:5]:
                print(f"     * {ch['title']}")
        else:
            print("   - No chapters detected (using strict mode).")

        # Chunking
        print("3️⃣  Chunking text...")
        chunks = processor.chunk_text(full_text, chunk_size=1000)
        print(f"   - Total Chunks: {len(chunks)}")
        
        # Average
        if len(chunks) > 0:
            avg_size = len(full_text) / len(chunks)
            print(f"   - Avg Chunk Size: {avg_size:.0f} chars")
            print(f"   - Chunks per page: {len(chunks) / extraction['page_count']:.2f}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Hardcoded path from user (file causing 4278 chunks)
    target_pdf = r"G:\ไดรฟ์ของฉัน\Library\Your Best Brain (John J. Medina) (Z-Library).pdf"
    analyze_pdf(target_pdf)
