"""
LangChain Chat Module with Memory
Provides conversational AI with persistent memory across turns.
"""
from typing import Generator, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory


class LangChainChat:
    """
    LangChain-powered chat with memory.
    Remembers conversation history for better context.
    """
    
    def _escape_braces(self, text: str) -> str:
        """Escape curly braces to prevent LangChain from treating them as variables."""
        if not text:
            return ""
        return text.replace("{", "{{").replace("}", "}}")
    
    def __init__(self, model: str = "llama3.1", memory_window: int = 10, num_ctx: int = 4096):
        """
        Initialize chat with memory.
        
        Args:
            model: Ollama model name
            memory_window: Number of conversation turns to remember
            num_ctx: Context window size
        """
        self.model_name = model
        self.memory_window = memory_window
        self.num_ctx = num_ctx
        self.llm = None
        self.memory = None
        self.context = None  # Optional document context
        
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LangChain LLM."""
        self.llm = ChatOllama(
            model=self.model_name,
            base_url="http://localhost:11434",
            timeout=300.0,
            num_ctx=self.num_ctx,
            num_gpu=999
        )
        
        # Conversation memory (simple in-memory history)
        self.chat_history = InMemoryChatMessageHistory()
    
    def set_model(self, model: str, num_ctx: int = None):
        """Change the model."""
        self.model_name = model
        if num_ctx:
            self.num_ctx = num_ctx
        self._init_llm()
    
    def set_context(self, context: str):
        """Set document context for the conversation."""
        self.context = context
    
    def clear_context(self):
        """Clear document context."""
        self.context = None
    
    def clear_memory(self):
        """Clear conversation history."""
        self.chat_history.clear()
    
    def get_memory_summary(self) -> str:
        """Get a summary of what's in memory."""
        messages = self.chat_history.messages
        return f"Remembering {len(messages)} messages"
    
    def chat(self, message: str, stream: bool = True) -> Generator[str, None, None] | str:
        """
        Chat with memory.
        
        Args:
            message: User's message
            stream: If True, yield response chunks
            
        Returns:
            Response string or generator
        """
        # Build system message
        system_parts = [
            "You are a helpful, knowledgeable AI assistant. You can answer questions on any topic, "
            "help with coding, explain concepts, and have natural conversations.",
            "",
            "Rules:",
            "1. Respond in the same language as the user's message",
            "2. Be conversational, helpful, and thorough",
            "3. If you don't know something, say so honestly",
            "4. Use markdown formatting when helpful"
        ]
        
        if self.context:
            system_parts.append("")
            system_parts.append("You have the following document context to reference:")
            system_parts.append(f"---\n{self._escape_braces(self.context[:4000])}\n---")
            system_parts.append("Use this context to answer questions when relevant.")
        
        system_message = "\n".join(system_parts)
        
        # Build messages list
        # We must escape braces in all content passed to ChatPromptTemplate.from_messages
        # because it treats the strings as templates.
        messages = [("system", self._escape_braces(system_message))]
        
        # Add memory (past conversation - keep last N*2 messages)
        history_messages = self.chat_history.messages
        # Keep last memory_window * 2 messages (each turn is 2 messages)
        recent_messages = history_messages[-(self.memory_window * 2):] if len(history_messages) > self.memory_window * 2 else history_messages
        for msg in recent_messages:
            content = self._escape_braces(msg.content)
            if isinstance(msg, HumanMessage):
                messages.append(("human", content))
            elif isinstance(msg, AIMessage):
                messages.append(("ai", content))
        
        # Add current message
        messages.append(("human", self._escape_braces(message)))
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # Generate response
        if stream:
            return self._stream_response(message, prompt)
        else:
            return self._generate_response(message, prompt)
    
    def _stream_response(self, user_message: str, prompt) -> Generator[str, None, None]:
        """Stream the response."""
        full_response = ""
        
        try:
            chain = prompt | self.llm
            
            for chunk in chain.stream({}):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += content
                yield content
            
            # Save to memory after complete
            self.chat_history.add_user_message(user_message)
            self.chat_history.add_ai_message(full_response)
            
        except Exception as e:
            yield f"\n\n❌ Error: {str(e)}"
    
    def _generate_response(self, user_message: str, prompt) -> str:
        """Generate non-streaming response."""
        try:
            chain = prompt | self.llm
            response = chain.invoke({})
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Save to memory
            self.chat_history.add_user_message(user_message)
            self.chat_history.add_ai_message(content)
            
            return content
            
        except Exception as e:
            return f"❌ Error: {str(e)}"


# Singleton instance for Streamlit session
_chat_instance = None

def get_chat_instance(model: str = "llama3.1", num_ctx: int = 4096) -> LangChainChat:
    """Get or create a chat instance."""
    global _chat_instance
    if _chat_instance is None or _chat_instance.model_name != model:
        _chat_instance = LangChainChat(model=model, num_ctx=num_ctx)
    return _chat_instance
