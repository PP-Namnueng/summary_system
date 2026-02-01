"""
LangChain Summarizer with MapReduce
Handles long documents by chunking and combining summaries.
"""
from typing import Generator, Optional, List
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class LangChainSummarizer:
    """
    LangChain-powered summarizer with MapReduce for long documents.
    """
    
    def __init__(self, model: str = "llama3.1", num_ctx: int = 4096):
        """
        Initialize summarizer.
        
        Args:
            model: Ollama model name
            num_ctx: Context window size
        """
        self.model_name = model
        self.num_ctx = num_ctx
        self.llm = None
        
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM."""
        self.llm = ChatOllama(
            model=self.model_name,
            base_url="http://localhost:11434",
            timeout=300.0,
            num_ctx=self.num_ctx
        )
    
    def set_model(self, model: str, num_ctx: int = None):
        """Change model."""
        self.model_name = model
        if num_ctx:
            self.num_ctx = num_ctx
        self._init_llm()
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of tokens (4 chars per token)."""
        return len(text) // 4
    
    def summarize(
        self, 
        text: str, 
        language: str = "Thai",
        stream: bool = True
    ) -> Generator[str, None, None] | str:
        """
        Summarize text, using MapReduce for long documents.
        
        Args:
            text: Text to summarize
            language: Output language
            stream: If True, stream the response
            
        Returns:
            Summary string or generator
        """
        estimated_tokens = self.estimate_tokens(text)
        
        # If short enough, use simple summarization
        if estimated_tokens < self.num_ctx * 0.6:
            return self._summarize_simple(text, language, stream)
        else:
            # Use MapReduce for long documents
            return self._summarize_mapreduce(text, language, stream)
    
    def _summarize_simple(
        self, 
        text: str, 
        language: str, 
        stream: bool
    ) -> Generator[str, None, None] | str:
        """Simple single-pass summarization."""
        prompt = f"""Summarize the following content comprehensively in {language}.

Guidelines:
1. Start with the main topic/title
2. Include all key points and concepts
3. Maintain the original structure where helpful
4. Use bullet points for clarity
5. Include any important data, quotes, or examples
6. End with key takeaways

Content:
{text}

Summary in {language}:"""

        if stream:
            return self._stream_llm(prompt)
        else:
            response = self.llm.invoke(prompt)
            return response.content

    def _summarize_mapreduce(
        self, 
        text: str, 
        language: str, 
        stream: bool
    ) -> Generator[str, None, None] | str:
        """MapReduce summarization for long documents."""
        
        # Split into chunks
        chunk_size = int(self.num_ctx * 0.5 * 4)  # Convert tokens to chars
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        texts = text_splitter.split_text(text)
        docs = [Document(page_content=t) for t in texts]
        
        if stream:
            # Stream the MapReduce process
            return self._stream_mapreduce(docs, language)
        else:
            # For non-streaming, collect all output
            result = ""
            for chunk in self._stream_mapreduce(docs, language):
                result += chunk
            return result
    
    def _stream_mapreduce(
        self, 
        docs: List[Document], 
        language: str
    ) -> Generator[str, None, None]:
        """Stream MapReduce summarization with progress updates."""
        
        yield f"📊 Processing {len(docs)} chunks...\n\n"
        
        # Phase 1: Map - Summarize each chunk
        chunk_summaries = []
        for i, doc in enumerate(docs):
            yield f"🔄 Summarizing chunk {i+1}/{len(docs)}...\n"
            
            map_prompt = f"""Summarize this section concisely in {language}:

{doc.page_content}

Summary:"""
            
            response = self.llm.invoke(map_prompt)
            chunk_summaries.append(response.content)
        
        yield f"\n✅ All chunks processed. Combining...\n\n---\n\n"
        
        # Phase 2: Reduce - Combine all summaries
        combined = "\n\n".join(chunk_summaries)
        
        reduce_prompt = f"""The following are summaries of different sections of a document.
Combine them into a comprehensive, well-organized summary in {language}.

Section summaries:
{combined}

Create a unified summary that:
1. Removes redundancy
2. Organizes information logically
3. Highlights key themes
4. Maintains important details

Combined Summary in {language}:"""

        # Stream the final reduction
        for chunk in self.llm.stream(reduce_prompt):
            yield chunk.content
    
    def _stream_llm(self, prompt: str) -> Generator[str, None, None]:
        """Stream LLM response."""
        for chunk in self.llm.stream(prompt):
            yield chunk.content


def get_summarizer(model: str = "llama3.1", num_ctx: int = 4096) -> LangChainSummarizer:
    """Factory function to get summarizer instance."""
    return LangChainSummarizer(model=model, num_ctx=num_ctx)
