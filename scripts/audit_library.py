import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.document_store import DocumentStore
from library.vector_store import VectorStore

def audit_library():
    print("🔍 Starting Library Audit...")
    
    # 1. Load Components
    try:
        doc_store = DocumentStore()
        vector_store = VectorStore()
    except Exception as e:
        print(f"❌ Error loading components: {e}")
        return

    docs = doc_store.list_documents()
    print(f"📚 Total Documents in Library: {len(docs)}")
    
    issues = []
    not_indexed = []
    missing_files = []
    
    # Infer source directory from first document
    source_dir = None
    if docs:
        first_path = Path(docs[0].get("file_path"))
        source_dir = first_path.parent
        print(f"📂 inferred Source Directory: {source_dir}")
        
    # Check for un-imported files (Exists on disk, but not in Library)
    unimported = []
    if source_dir and source_dir.exists():
        disk_pdfs = list(source_dir.glob("*.pdf")) + list(source_dir.glob("**/*.pdf"))
        # Normalize paths for comparison
        lib_filenames = {d.get("filename") for d in docs}
        
        for p in disk_pdfs:
            if p.name not in lib_filenames:
                unimported.append(p.name)
    
    # 2. Check Integrity
    for doc in docs:
        doc_id = doc.get("doc_id")
        filename = doc.get("filename")
        file_path = doc.get("file_path")
        indexed = doc.get("indexed", False)
        
        # Check File Existence
        if not os.path.exists(file_path):
            missing_files.append(f"{filename} (Path: {file_path})")
            issues.append(f"❌ MISSING FILE: {filename}")
            continue
            
        # Check Indexed Status
        if not indexed:
            not_indexed.append(filename)
        else:
            # Optional: Check if chunks > 0
            chunks = doc.get("chunk_count", 0)
            if chunks == 0:
                issues.append(f"⚠️ INDEXED BUT 0 CHUNKS: {filename}")

    # Create report string
    report = []
    report.append("\n--- 📊 Audit Report ---")
    
    if missing_files:
        report.append(f"\n❌ Missing Files ({len(missing_files)}):")
        for f in missing_files:
            report.append(f"   - {f}")
        report.append("   (Action: Delete these from library to clean up)")
        
    if unimported:
        report.append(f"\n❓ Un-Imported Files ({len(unimported)}):")
        for f in unimported:
             report.append(f"   - {f}")
        report.append("   (Action: These files exist on disk but are NOT in the library. Run Import!)")
    else:
        report.append("\n✅ All source files are tracked in library.")
    
    if not_indexed:
        report.append(f"\n⏳ Not Indexed Yet ({len(not_indexed)}):")
        for f in not_indexed:
             # Re-fetch doc to get details
            doc = next((d for d in docs if d["filename"] == f), None)
            if doc:
                size_mb = doc.get("file_size_bytes", 0) / (1024 * 1024)
                report.append(f"   - 📄 {f}")
                report.append(f"     Size: {size_mb:.2f} MB")
                report.append(f"     Path: {doc.get('file_path')}")
                report.append(f"     Date Added: {doc.get('added_date')}")
        report.append("   (Action: Run Import again to process these)")
    else:
        report.append("\n✅ All documents are marked as indexed.")
        
    if issues:
        report.append(f"\n⚠️ Other Issues ({len(issues)}):")
        for i in issues:
            report.append(f"   - {i}")
            
    # 4. Vector Store Stats
    stats = vector_store.get_stats()
    report.append(f"\n🧠 Vector Database Stats:")
    report.append(f"   - Total Chunks: {stats.get('total_chunks', 'Unknown')}")
    report.append(f"   - Model: {stats.get('embedding_model', 'Unknown')}")
    
    final_report = "\n".join(report)
    print(final_report)
    
    with open("audit_report.txt", "w", encoding="utf-8") as f:
        f.write(final_report)

if __name__ == "__main__":
    audit_library()
