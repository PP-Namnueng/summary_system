import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from summarizer.ollama_client import OllamaSummarizer
from library.vector_store import VectorStore

def test_summarizer():
    print("\n--- Testing Summarizer (OllamaClient) ---")
    print("Allocating generic request with 'num_gpu': 999...")
    
    try:
        # Initialize
        summ = OllamaSummarizer()
        print(f"Model detected: {summ.model}")
        
        # Simple generation
        text = "The quick brown fox jumps over the lazy dog. " * 20
        start_time = time.time()
        print("Sending request to Ollama...")
        
        result = summ.summarize(text, language="en", content_type="test_phrase")
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.get("success"):
            print(f"✅ Success! Response received in {duration:.2f} seconds.")
            print(f"Sample: {result['summary'][:100]}...")
        else:
            print(f"❌ Failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception during summarizer test: {e}")

def test_embedding():
    print("\n--- Testing VectorStore (Embeddings) ---")
    print("Allocating embedding request with 'num_gpu': 999...")
    
    try:
        # Initialize
        vs = VectorStore()
        print(f"Embedding Model: {vs.embedding_model}")
        
        # Create dummy chunk
        chunks = [{
            "text": "Artificial intelligence with GPU acceleration is fast.",
            "chunk_index": 0,
            "chapter": "Test Chapter"
        }]
        
        start_time = time.time()
        print("Sending embedding request to Ollama...")
        
        # Index
        result = vs.index_document("test_gpu_verification", chunks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.get("success"):
            print(f"✅ Success! Embedded {result['indexed_chunks']} chunks in {duration:.2f} seconds.")
        else:
            print(f"❌ Failed: {result.get('error')}")
            
        # Cleanup
        vs.delete_document_chunks("test_gpu_verification")
        
    except Exception as e:
        print(f"❌ Exception during embedding test: {e}")

if __name__ == "__main__":
    print("🚀 Starting GPU Configuration Verification Script")
    print("Please monitor your Task Manager (Performance > GPU) or 'nvidia-smi' now.")
    
    test_summarizer()
    test_embedding()
    
    print("\nDone.")
