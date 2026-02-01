"""
Ollama LLM client for summarization
"""
import ollama
import httpx
from typing import Optional, Generator


class OllamaSummarizer:
    """Generate summaries using Ollama local LLM"""

    # Default models to try (in order of preference for Thai language)
    PREFERRED_MODELS = [
        "typhoon",      # Best for Thai
        "gemma3",       # Good multilingual
        "gemma2",       # Good multilingual  
        "llama3.2",
        "llama3.1", 
        "llama3",
        "mistral",
        "qwen",         # May output Chinese, lower priority
    ]

    def __init__(self, model: str = None, timeout: int = 600, num_ctx: int = 4096):
        """
        Initialize Ollama summarizer
        
        Args:
            model: Specific model to use (if None, auto-detect)
            timeout: Request timeout in seconds (default 600s = 10 min)
            num_ctx: Context window size (default 4096)
        """
        self.model = model
        self.timeout = timeout
        self.num_ctx = num_ctx
        
        # Create httpx client with very long timeout for LLM generation
        try:
            http_client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=30.0,      # 30s to connect
                    read=600.0,        # 10 min to read (for slow generation)
                    write=30.0,        # 30s to write
                    pool=None          # No pool timeout
                )
            )
            self.client = ollama.Client(http_client=http_client)
        except (TypeError, Exception):
            # Fallback for older ollama versions
            try:
                self.client = ollama.Client(timeout=timeout)
            except TypeError:
                self.client = ollama.Client()
        
        if not self.model:
            self.model = self._detect_model()

    def _detect_model(self) -> str:
        """Auto-detect available model"""
        try:
            response = self.client.list()
            # Handle new ollama package that returns objects
            if hasattr(response, 'models'):
                available = [m.model.split(":")[0] for m in response.models]
            else:
                available = [m["name"].split(":")[0] for m in response.get("models", [])]
            
            # Try preferred models first
            for preferred in self.PREFERRED_MODELS:
                for avail in available:
                    if preferred in avail.lower():
                        return avail
            
            # Return first available model
            if available:
                return available[0]
            
            return "llama3.2"  # Default fallback
        except Exception:
            return "llama3.2"

    def _get_thai_summary_prompt(self, content: str, content_type: str = "content") -> str:
        """Get prompt for Thai summarization (Professor Mode)"""
        return f"""[IMPORTANT: ตอบเป็นภาษาไทยเท่านั้น โดยสวมบทบาทอาจารย์มหาวิทยาลัยผู้เชี่ยวชาญ]

บทบาทของคุณ: ศาสตราจารย์ผู้เชี่ยวชาญที่สามารถอธิบายเรื่องซับซ้อนให้เข้าใจง่าย ลึกซึ้ง และมีโครงสร้างชัดเจน

กระบวนการคิด (Chain of Thought):
1. อ่านเนื้อหาทั้งหมดและจับใจความสำคัญหลัก (Core Concept)
2. วิเคราะห์โครงสร้างของเนื้อหา แยกเป็นประเด็นย่อย
3. กลั่นกรองเฉพาะ "เนื้อหาเนื้อๆ" ที่สำคัญ ตัดน้ำออก
4. เรียบเรียงใหม่ด้วยภาษาที่สละสลวย เข้าใจง่าย แต่คงไว้ซึ่งความถูกต้องทางวิชาการ

คำสั่งการสรุป:
1. **ห้ามแปลตรงตัว**: ให้เรียบเรียงใหม่ (Paraphrase) ให้เป็นภาษาไทยที่ลื่นไหลเป็นธรรมชาติ
2. **เจาะลึก**: อย่าเขียนแค่ผิวเผิน ให้อธิบาย "เหตุผล" และ "ที่มาที่ไป" ของแต่ละประเด็น
3. **โครงสร้าง**: จัดแบ่งให้อ่านง่าย มีหัวข้อ (Heading) และข้อย่อย (Bullet points)
4. **Emoji**: ใช้ประกอบหัวข้อหลักพอสังเขป เพื่อให้น่าอ่าน (Professional usage)

รูปแบบการนำเสนอ:

## 🎓 ภาพรวมของเนื้อหา 
[สรุปภาพรวมและใจความสำคัญของเนื้อหาให้คนที่อ่านสมารถมองเห็นภาพรวมของเนื้อหาได้ทันที]

## 🔑 ประเด็นวิเคราะห์เจาะลึก (Key Insights & Analysis)
[จุดนี้คือหัวใจสำคัญ ให้แยกเป็นประเด็นๆ]
### 1. [ชื่อประเด็นที่ 1]
- อธิบายรายละเอียดเชิงลึก...
- ทำไมถึงสำคัญ? ...

### 2. [ชื่อประเด็นที่ 2]
- อธิบายรายละเอียดเชิงลึก...
...

## 💡 บทเรียนและข้อคิด (Key Takeaways)
- [สิ่งที่ผู้อ่านควรจำนำไปใช้]
- [ข้อควรระวังหรือคำแนะนำเพิ่มเติม]

## 📚 แหล่งเรียนรู้ต่อยอด (Recommended Resources)
- **[ชื่อหนังสือ / คอร์ส / แหล่งข้อมูล]**: [ระบุชื่อ]
  - *ทำไมถึงแนะนำ?*: [อธิบายเหตุผลว่าทำไมแหล่งนี้ถึงดี หรือเหมาะกับหัวข้อนี้]
  - *เหมาะสำหรับ*: [ระบุระดับ เช่น ผู้เริ่มต้น / ผู้เชี่ยวชาญ]

---
เนื้อหาต้นฉบับ ({content_type}):
{content}
"""

    def _get_english_summary_prompt(self, content: str, content_type: str = "content") -> str:
        """Get prompt for English summarization (Analyst Mode)"""
        return f"""[ROLE: Senior Strategic Analyst]

Task: Analyze the provided content and produce a high-value Intelligence Report.

Thinking Process:
1. Deconstruct the content into core arguments and supporting evidence.
2. Identify the "Signal" amidst the "Noise".
3. Synthesize findings into actionable insights.

Instructions:
1. **Focus on Value**: Don't just summarize *what* was said, explain *why* it matters.
2. **Clarity**: Use precise, professional business English.
3. **Structure**: Use clear hierarchy (Headers > Subheaders > Bullets).

Report Format:

## 📋 Executive Brief
[High-level synthesis of the main message. max 3-4 sentences.]

## � Strategic Analysis
### [Core Theme 1]
- **Insight**: [Detailed explanation of the point]
- **Implication**: [Why this matters / Context]

### [Core Theme 2]
- **Insight**: ...

## � Actionable Takeaways
- [Specific point 1]
- [Specific point 2]

## 📚 Recommended Learning Path
- **[Resource Name]** (Book/Article/Course):
  - *Why it's highly recommended*: [Explain the unique value recommendation]
  - *Context*: [How it connects to this topic]

---
Source Material ({content_type}):
{content}
"""

    def _chunk_content(self, content: str, max_chars: int = 8000) -> list[str]:
        """Split content into chunks for long documents"""
        if len(content) <= max_chars:
            return [content]
        
        chunks = []
        paragraphs = content.split("\n\n")
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def summarize(
        self,
        content: str,
        language: str = "th",
        content_type: str = "content",
        stream: bool = False,
        template: str = "standard",
    ) -> dict | Generator:
        """
        Generate summary for given content
        
        Args:
            content: Text content to summarize
            language: Output language ('th' for Thai, 'en' for English)
            content_type: Type of content (for context in prompt)
            stream: Whether to stream the response
            template: Summary style ('standard', 'executive', 'technical', 'eli5')
            
        Returns:
            dict with summary or generator for streaming
        """
        if not content or not content.strip():
            return {
                "summary": "",
                "error": "No content provided",
                "success": False,
            }
        
        # Get appropriate prompt based on template
        if template == "executive":
            prompt = self._get_executive_prompt(content, content_type, language)
        elif template == "technical":
            prompt = self._get_technical_prompt(content, content_type, language)
        elif template == "eli5":
            prompt = self._get_eli5_prompt(content, content_type, language)
        elif language == "th":
            prompt = self._get_thai_summary_prompt(content, content_type)
        else:
            prompt = self._get_english_summary_prompt(content, content_type)
        
        try:
            if stream:
                return self._stream_response(prompt)
            else:
                return self._generate_response(prompt)
        except Exception as e:
            return {
                "summary": "",
                "error": f"LLM error: {str(e)}",
                "success": False,
            }
    
    def _get_executive_prompt(self, content: str, content_type: str, language: str) -> str:
        """Executive summary prompt - business-focused, decisions & impact"""
        lang_instruction = "ตอบเป็นภาษาไทย" if language == "th" else "Respond in English"
        return f"""[{lang_instruction}]

Role: You are a Senior Business Analyst preparing a briefing for C-level executives.

Task: Create an EXECUTIVE SUMMARY focused on business impact, decisions, and actionable insights.

Format:
## 📊 Executive Summary
[One paragraph: What is this about and why does it matter?]

## 💰 Business Impact
- [Key impacts on revenue, costs, or competitive advantage]
- [Market implications]

## ✅ Key Decisions Required
1. [Decision point 1]
2. [Decision point 2]

## ⚡ Recommended Actions
- [Immediate action]
- [Short-term action]
- [Long-term consideration]

## ⚠️ Risks & Considerations
- [Key risks]

---
Source ({content_type}):
{content}
"""

    def _get_technical_prompt(self, content: str, content_type: str, language: str) -> str:
        """Technical deep-dive prompt - detailed architecture and implementation"""
        lang_instruction = "ตอบเป็นภาษาไทย" if language == "th" else "Respond in English"
        return f"""[{lang_instruction}]

Role: You are a Senior Technical Architect writing documentation for engineers.

Task: Create a TECHNICAL DEEP-DIVE with implementation details, architecture, and code examples.

Format:
## 🔧 Technical Overview
[Technical description of the system/concept]

## 🏗️ Architecture & Components
- [Component 1]: [Description]
- [Component 2]: [Description]

## 💻 Implementation Details
```
[Code example or pseudo-code if applicable]
```

## 📈 Performance Considerations
- [Scalability notes]
- [Optimization opportunities]

## 🔌 Integration Points
- [APIs, protocols, dependencies]

## 📋 Technical Requirements
- [Prerequisites]
- [Dependencies]

---
Source ({content_type}):
{content}
"""

    def _get_eli5_prompt(self, content: str, content_type: str, language: str) -> str:
        """ELI5 prompt - simple explanation for everyone"""
        lang_instruction = "ตอบเป็นภาษาไทย" if language == "th" else "Respond in English"
        return f"""[{lang_instruction}]

Role: You are a friendly teacher explaining complex topics to a curious 5-year-old.

Task: Create an ELI5 (Explain Like I'm 5) summary using simple words, analogies, and fun examples.

Rules:
1. NO jargon - use everyday words
2. Use analogies (like "it's like when...")
3. Use emojis to make it fun
4. Keep sentences short
5. Use examples from daily life

Format:
## 🎈 What is this about?
[Simple one-sentence explanation]

## 🧩 How does it work?
[Explain like telling a story to a child]

## 🍎 Real-life example
[Analogy using something everyone knows]

## 🌟 Why should we care?
[Simple reason why this matters]

## 🎯 The main point
[One simple takeaway]

---
Source ({content_type}):
{content}
"""
            
    def _get_chat_prompt(self, message: str, context: str = None, history: list[dict] = None) -> str:
        """Get prompt for chat interactions - works with or without context"""
        history_text = ""
        if history:
            for msg in history[-5:]:  # Keep last 5 turns
                role = "User" if msg["role"] == "user" else "Assistant"
                history_text += f"{role}: {msg['content']}\n"
        
        # Build context section only if content is available
        if context and context.strip():
            context_section = f"""Reference Content (use if relevant to the question):
{context[:self.num_ctx * 4]}
"""
            context_instruction = "If the question relates to the reference content above, incorporate that information. Otherwise, use your general knowledge."
        else:
            context_section = ""
            context_instruction = "Answer using your general knowledge and expertise."
        
        return f"""You are a helpful, knowledgeable AI assistant. You can answer questions on any topic using your broad knowledge.

{context_section}
Previous Conversation:
{history_text}

Current Question: {message}

Instructions:
1. {context_instruction}
2. Be thorough but concise. Provide detailed explanations when needed.
3. Response in the same language as the question (Thai or English).
4. If you're unsure about something, acknowledge it honestly.

Answer:"""

    def chat(
        self,
        message: str,
        context: str = None,
        history: list[dict] = None,
        stream: bool = False,
    ) -> dict | Generator:
        """
        Chat with or without content context. Works as general knowledge assistant.
        """
        if not message:
            return {
                "response": "Missing message",
                "success": False
            }

        prompt = self._get_chat_prompt(message, context, history)
        
        try:
            if stream:
                return self._stream_response(prompt)
            else:
                return self._generate_response(prompt)
        except Exception as e:
            return {
                "response": "",
                "error": f"Chat error: {str(e)}",
                "success": False
            }

    def _generate_response(self, prompt: str) -> dict:
        """Generate non-streaming response"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 16384,     # Max generation (safe limit)
                    "num_ctx": self.num_ctx,          # Dynamic context size
                    "num_batch": 512,         # Faster batch processing
                    "num_gpu": 999,           # Force GPU usage
                }
            )
            
            # Handle new ollama package that returns objects
            if hasattr(response, 'response'):
                text = response.response
            else:
                text = response["response"]
            
            return {
                "summary": text,
                "model": self.model,
                "success": True,
            }
        except Exception as e:
            return {
                "summary": "",
                "error": str(e),
                "success": False,
            }

    def _stream_response(self, prompt: str) -> Generator:
        """Generate streaming response"""
        try:
            stream = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=True,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 16384,     # Max generation (safe limit)
                    "num_ctx": self.num_ctx,          # Dynamic context size
                    "num_batch": 512,         # Faster batch processing
                    "num_gpu": 999,           # Force GPU usage
                }
            )
            
            for chunk in stream:
                # Handle new ollama package that returns objects
                if hasattr(chunk, 'response'):
                    yield chunk.response or ""
                else:
                    yield chunk.get("response", "")
                
        except Exception as e:
            yield f"\n\n❌ Error: {str(e)}"

    def summarize_long_content(
        self,
        content: str,
        language: str = "th",
        content_type: str = "content",
    ) -> dict:
        """
        Summarize long content by chunking and combining
        
        Args:
            content: Long text content
            language: Output language
            content_type: Type of content
            
        Returns:
            dict with combined summary
        """
        chunks = self._chunk_content(content)
        
        if len(chunks) == 1:
            return self.summarize(content, language, content_type)
        
        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            result = self.summarize(
                chunk, 
                language, 
                f"{content_type} (Part {i+1}/{len(chunks)})"
            )
            if result["success"]:
                chunk_summaries.append(result["summary"])
        
        if not chunk_summaries:
            return {
                "summary": "",
                "error": "Failed to summarize content chunks",
                "success": False,
            }
        
        # Combine chunk summaries into final summary
        combined = "\n\n---\n\n".join(chunk_summaries)
        
        # Create final summary of summaries (Enhanced)
        if language == "th":
            final_prompt = f"""[IMPORTANT: รวมสรุปทั้งหมดให้เป็น "สรุปฉบับสมบูรณ์" ที่ละเอียดที่สุด]
            
สรุปย่อยจากส่วนต่างๆ:
{combined}

คำสั่ง:
1. รวมเนื้อหาทั้งหมดเข้าด้วยกัน จัดลำดับให้ต่อเนื่องและเข้าใจง่าย
2. **ห้ามตัดทอนรายละเอียดสำคัญ**: คงเนื้อหาเชิงลึกจากสรุปย่อยไว้ให้ครบถ้วน
3. ใช้โครงสร้างเดียวกับสรุปย่อย (Overview, Key Points, Details)
4. ใช้ Emoji ตกแต่งให้น่าอ่านไม่มากจนเกินไปเน้นความ casual แต่อ่านง่าย
5. ความยาว: ไม่จำกัด (เน้นความครบถ้วน)

เริ่มเขียนสรุปฉบับรวม:"""
        else:
             final_prompt = f"""[IMPORTANT: Combine into a highly detailed MASTER SUMMARY]

Partial Summaries:
{combined}

Instructions:
1. Merge all sections into a seamless narrative.
2. **RETAIN ALL DETAILS**: Do not simplify too much. The goal is comprehensiveness.
3. Maintain the structured format.
4. Use standard Emoji decoration.

Start writing Master Summary:"""
        
        return self._generate_response(final_prompt)

    def get_available_models(self) -> list[str]:
        """Get list of available Ollama models"""
        try:
            response = self.client.list()
            # Handle new ollama package that returns objects
            if hasattr(response, 'models'):
                return [m.model for m in response.models]
            else:
                return [m["name"] for m in response.get("models", [])]
        except Exception:
            return []

    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            self.client.list()
            return True
        except Exception:
            return False
