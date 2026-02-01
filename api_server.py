"""
FastAPI Backend Server for Knowledge Summary System
Run with: uvicorn api_server:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio

# Import our modules
from summarizer import OllamaSummarizer
from extractors import YouTubeExtractor, WebPageExtractor, PDFExtractor
from agents.research_agent import ResearchAgent
from library import DocumentStore, VectorStore, RAGEngine

# Initialize FastAPI
app = FastAPI(
    title="Knowledge Summary API",
    description="API for summarization, chat, research, and library management",
    version="1.0.0"
)

# CORS for mobile/web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global instances
summarizer = None
doc_store = None
vector_store = None
rag_engine = None


def get_summarizer(model: str = "llama3.1", ctx_size: int = 8192) -> OllamaSummarizer:
    """Get or create summarizer instance."""
    global summarizer
    if summarizer is None or summarizer.model != model:
        summarizer = OllamaSummarizer(model=model, num_ctx=ctx_size)
    return summarizer


def get_doc_store() -> DocumentStore:
    """Get document store instance."""
    global doc_store
    if doc_store is None:
        doc_store = DocumentStore()
    return doc_store


def get_vector_store() -> VectorStore:
    """Get vector store instance."""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store


def get_rag_engine() -> RAGEngine:
    """Get RAG engine instance."""
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine(
            document_store=get_doc_store(),
            vector_store=get_vector_store()
        )
    return rag_engine


# ============== Request/Response Models ==============

class SummarizeRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None
    language: str = "th"
    template: str = "standard"  # standard, executive, technical, eli5
    model: str = "llama3.1"
    ctx_size: int = 8192


class SummarizeResponse(BaseModel):
    success: bool
    summary: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None
    history: Optional[List[dict]] = None
    model: str = "llama3.1"
    use_library_rag: bool = False


class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None


class ResearchRequest(BaseModel):
    topic: str
    language: str = "th"
    max_sources: int = 5
    model: str = "llama3.1"


class ResearchResponse(BaseModel):
    success: bool
    report: Optional[str] = None
    sources: Optional[List[dict]] = None
    error: Optional[str] = None


class LibrarySearchRequest(BaseModel):
    query: str
    top_k: int = 5


class LibrarySearchResponse(BaseModel):
    success: bool
    results: Optional[List[dict]] = None
    error: Optional[str] = None


class LibraryStatsResponse(BaseModel):
    total_documents: int
    indexed_documents: int
    total_chunks: int


# ============== API Endpoints ==============

@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "online",
        "service": "Knowledge Summary API",
        "version": "1.0.0",
        "endpoints": [
            "/summarize",
            "/chat",
            "/research",
            "/library/search",
            "/library/stats"
        ]
    }


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """
    Summarize content from URL or text.
    
    - **url**: YouTube or website URL to summarize
    - **text**: Direct text to summarize (if no URL)
    - **language**: Output language (th/en)
    - **template**: Summary style (standard/executive/technical/eli5)
    """
    try:
        content = ""
        title = None
        
        # Extract content from URL if provided
        if request.url:
            # Detect type
            if "youtube" in request.url or "youtu.be" in request.url:
                extractor = YouTubeExtractor()
            else:
                extractor = WebPageExtractor()
            
            result = extractor.extract(request.url)
            if not result.get("success"):
                return SummarizeResponse(success=False, error=result.get("error", "Extraction failed"))
            
            content = result.get("text", "")
            title = result.get("title")
        elif request.text:
            content = request.text
        else:
            return SummarizeResponse(success=False, error="No URL or text provided")
        
        # Summarize
        summarizer = get_summarizer(request.model, request.ctx_size)
        result = summarizer.summarize(
            content=content,
            language=request.language,
            template=request.template,
            stream=False
        )
        
        if result.get("success"):
            return SummarizeResponse(
                success=True,
                summary=result.get("summary"),
                title=title
            )
        else:
            return SummarizeResponse(success=False, error=result.get("error"))
            
    except Exception as e:
        return SummarizeResponse(success=False, error=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI assistant.
    
    - **message**: User message
    - **context**: Optional context text
    - **history**: Optional conversation history
    - **use_library_rag**: Search library for context
    """
    try:
        summarizer = get_summarizer(request.model)
        
        context = request.context
        
        # If library RAG enabled, search for context
        if request.use_library_rag and not context:
            try:
                vs = get_vector_store()
                results = vs.search(request.message, top_k=3)
                if results:
                    context = "\n\n".join([
                        f"From '{r.get('title', 'Unknown')}': {r.get('text', '')[:500]}"
                        for r in results
                    ])
            except Exception:
                pass
        
        # Chat
        result = summarizer.chat(
            message=request.message,
            context=context,
            history=request.history,
            stream=False
        )
        
        if result.get("success"):
            return ChatResponse(
                success=True,
                response=result.get("summary")
            )
        else:
            return ChatResponse(success=False, error=result.get("error"))
            
    except Exception as e:
        return ChatResponse(success=False, error=str(e))


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Research a topic using web search.
    
    - **topic**: Topic to research
    - **language**: Output language
    - **max_sources**: Maximum sources to fetch
    """
    try:
        summarizer = get_summarizer(request.model)
        agent = ResearchAgent(summarizer=summarizer)
        
        # Collect results (non-streaming)
        full_report = ""
        sources = []
        
        for update in agent.research_topic(
            topic=request.topic,
            max_sources=request.max_sources,
            language=request.language
        ):
            if isinstance(update, str):
                continue  # Status update
            elif isinstance(update, dict):
                if update["type"] == "chunk":
                    full_report += update["content"]
                elif update["type"] == "sources":
                    sources = update.get("sources", [])
        
        return ResearchResponse(
            success=True,
            report=full_report,
            sources=sources
        )
        
    except Exception as e:
        return ResearchResponse(success=False, error=str(e))


@app.post("/library/search", response_model=LibrarySearchResponse)
async def library_search(request: LibrarySearchRequest):
    """
    Search the document library.
    
    - **query**: Search query
    - **top_k**: Number of results to return
    """
    try:
        vs = get_vector_store()
        results = vs.search(request.query, top_k=request.top_k)
        
        return LibrarySearchResponse(
            success=True,
            results=results
        )
        
    except Exception as e:
        return LibrarySearchResponse(success=False, error=str(e))


@app.get("/library/stats", response_model=LibraryStatsResponse)
async def library_stats():
    """Get library statistics."""
    try:
        ds = get_doc_store()
        vs = get_vector_store()
        
        doc_stats = ds.get_stats()
        vec_stats = vs.get_stats()
        
        return LibraryStatsResponse(
            total_documents=doc_stats.get("total_documents", 0),
            indexed_documents=doc_stats.get("indexed_documents", 0),
            total_chunks=vec_stats.get("total_chunks", 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/library/documents")
async def library_documents():
    """List all documents in the library."""
    try:
        ds = get_doc_store()
        documents = ds.list_documents()
        return {"success": True, "documents": documents}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/models")
async def list_models():
    """List available Ollama models."""
    try:
        summarizer = get_summarizer()
        models = summarizer.get_available_models()
        return {"success": True, "models": models}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============== New Endpoints ==============

@app.get("/sentinel/sources")
async def sentinel_sources():
    """Get Sentinel monitoring sources configuration."""
    try:
        import json
        from pathlib import Path
        sources_path = Path("data/sources.json")
        if sources_path.exists():
            with open(sources_path, "r", encoding="utf-8") as f:
                sources = json.load(f)
            return {"success": True, "sources": sources}
        return {"success": True, "sources": []}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/sentinel/trending")
async def sentinel_trending():
    """Get latest trending items from Sentinel."""
    try:
        from agents.sentinel import SentinelAgent
        sentinel = SentinelAgent()
        trending = sentinel.get_trending()
        return {"success": True, "trending": trending}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/sentinel/scan")
async def sentinel_scan():
    """Trigger a Sentinel scan for new content."""
    try:
        from agents.sentinel import SentinelAgent
        sentinel = SentinelAgent()
        results = sentinel.scan_sources()
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


class TTSRequest(BaseModel):
    text: str
    voice: str = "th-TH-NiwatNeural"
    output_name: Optional[str] = None


@app.post("/tts/generate")
async def tts_generate(request: TTSRequest):
    """Generate TTS audio from text."""
    try:
        from generators.edge_tts_runner import EdgeTTSRunner
        import uuid
        
        runner = EdgeTTSRunner()
        output_name = request.output_name or f"tts_{uuid.uuid4().hex[:8]}"
        output_path = f"sentinel_outputs/{output_name}.mp3"
        
        result = runner.generate(
            text=request.text,
            voice=request.voice,
            output_path=output_path
        )
        
        return {
            "success": True,
            "audio_path": output_path,
            "voice": request.voice
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/tts/voices")
async def tts_voices():
    """List available TTS voices."""
    voices = [
        {"id": "th-TH-NiwatNeural", "name": "Niwat (Thai Male)", "language": "th"},
        {"id": "th-TH-PremwadeeNeural", "name": "Premwadee (Thai Female)", "language": "th"},
        {"id": "en-US-GuyNeural", "name": "Guy (English Male)", "language": "en"},
        {"id": "en-US-JennyNeural", "name": "Jenny (English Female)", "language": "en"},
    ]
    return {"success": True, "voices": voices}


class ObsidianExportRequest(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None


@app.post("/obsidian/export")
async def obsidian_export(request: ObsidianExportRequest):
    """Export content to Obsidian vault."""
    try:
        from integrations.obsidian import ObsidianIntegration
        
        obsidian = ObsidianIntegration()
        result = obsidian.export_note(
            title=request.title,
            content=request.content,
            tags=request.tags or []
        )
        
        return {"success": True, "path": result.get("path")}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/obsidian/status")
async def obsidian_status():
    """Check Obsidian vault configuration."""
    try:
        from integrations.obsidian import ObsidianIntegration
        obsidian = ObsidianIntegration()
        return {
            "success": True,
            "configured": obsidian.is_configured(),
            "vault_path": str(obsidian.vault_path) if hasattr(obsidian, 'vault_path') else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


from fastapi import UploadFile, File


@app.post("/library/upload")
async def library_upload(file: UploadFile = File(...)):
    """Upload a PDF to the library."""
    try:
        import tempfile
        import shutil
        from pathlib import Path
        
        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Process the PDF
        from library.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        result = processor.process(tmp_path, title=file.filename)
        
        # Add to document store
        ds = get_doc_store()
        doc_id = ds.add_document(
            title=file.filename,
            content=result.get("text", ""),
            metadata={"source": "upload", "original_filename": file.filename}
        )
        
        # Index in vector store
        vs = get_vector_store()
        vs.add_document(doc_id, result.get("text", ""), metadata={"title": file.filename})
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "pages": result.get("pages", 0)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============== Run Server ==============

if __name__ == "__main__":
    import uvicorn
    print("Starting Knowledge Summary API...")
    print("Docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
