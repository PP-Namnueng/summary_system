import streamlit as st
import asyncio
import datetime
import os
import tempfile
import re
from itertools import groupby
from summary.summarizer import OllamaSummarizer
from summary.generators.podcast_generator import PodcastGenerator
from summary.agents.research_agent import ResearchAgent
from summary.integrations import ObsidianIntegration
from summary.extractors import YouTubeExtractor, WebPageExtractor, PDFExtractor
from summary.library import DocumentStore, PDFProcessor, VectorStore, RAGEngine

def detect_content_type(url: str) -> str:
    """Auto-detect content type from URL"""
    if not url:
        return "text"
    
    youtube_patterns = [
        r"youtube\.com",
        r"youtu\.be",
    ]
    
    for pattern in youtube_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return "youtube"
    
    if url.lower().endswith(".pdf"):
        return "pdf"
    
    if url.startswith("http"):
        return "webpage"
    
    return "text"


def extract_content(source_type: str, source: str | bytes, filename: str = None) -> dict:
    """Extract content based on source type"""
    if source_type == "youtube":
        extractor = YouTubeExtractor()
        return extractor.extract(source)
    
    elif source_type == "webpage":
        extractor = WebPageExtractor()
        return extractor.extract(source)
    
    elif source_type == "pdf":
        extractor = PDFExtractor()
        if isinstance(source, bytes):
            return extractor.extract_from_bytes(source, filename)
        else:
            return extractor.extract_from_file(source)
    
    elif source_type == "text":
        return {
            "text": source,
            "success": True,
        }
    
    return {"text": "", "error": "Unknown source type", "success": False}


def render_home_page():
    """Render the Home Landing Page"""
    st.title("🏠 Welcome Home")
    
    st.markdown("""
    <style>
        @keyframes shine {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes floating {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        .hero-title {
            background: linear-gradient(to right, #ffffff, #94a3b8, #ffffff);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shine 5s linear infinite;
            text-shadow: 0 0 40px rgba(255, 255, 255, 0.1);
        }
        .hero-icon {
            animation: floating 3s ease-in-out infinite;
            display: inline-block;
            filter: drop-shadow(0 0 15px rgba(255, 75, 75, 0.4));
        }
    </style>
    <div style='text-align: center; margin-bottom: 50px; padding-top: 30px;'>
        <div class="hero-icon" style="font-size: 4em; margin-bottom: 20px;">🧠</div>
        <h1 class="hero-title" style='font-size: 5.5em; font-weight: 900; margin: 0; letter-spacing: -3px; line-height: 1.0;'>
            Knowledge Summary
        </h1>
        <div style='font-size: 1.1em; font-weight: 500; letter-spacing: 5px; text-transform: uppercase; margin-top: 20px; color: #64748b; font-family: monospace;'>
            <span style='color: #ff4b4b; text-shadow: 0 0 10px rgba(255, 75, 75, 0.3);'>EXTRACT</span> 
            <span style='opacity: 0.3; margin: 0 15px;'>//</span> 
            <span style='color: #ff4b4b; text-shadow: 0 0 10px rgba(255, 75, 75, 0.3);'>SUMMARIZE</span> 
            <span style='opacity: 0.3; margin: 0 15px;'>//</span> 
            <span style='color: #ff4b4b; text-shadow: 0 0 10px rgba(255, 75, 75, 0.3);'>CHAT</span> 
            <span style='opacity: 0.3; margin: 0 15px;'>//</span> 
            <span style='color: #ff4b4b; text-shadow: 0 0 10px rgba(255, 75, 75, 0.3);'>LISTEN</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Dashboard Stats Section
    st.markdown("### 📊 Your Activity Dashboard")
    
    # Get stats from various sources
    try:
        doc_store = DocumentStore()
        library_stats = doc_store.get_stats()
        books_count = library_stats.get("total_documents", 0)
        indexed_count = library_stats.get("indexed_documents", 0)
    except Exception:
        books_count = 0
        indexed_count = 0
    
    # Count research reports (from session state)
    research_count = 1 if st.session_state.get("research_report") else 0
    
    # Chat messages count
    chat_count = len(st.session_state.get("chat_history", []))
    
    # Summaries count (from session state)
    summaries_count = 1 if st.session_state.get("summary_result") else 0
    
    # Display stats in columns
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        st.metric("📚 Library Books", books_count, f"{indexed_count} indexed")
    
    with col_b:
        st.metric("🕵️ Research Reports", research_count)
    
    with col_c:
        st.metric("💬 Chat Messages", chat_count)
    
    with col_d:
        st.metric("📝 Summaries", summaries_count)
    
    st.divider()

    # Central Input Container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container(border=True):
            st.markdown("### 🚀 Quick Start")
            
            input_method = st.radio(
                "Input Type", 
                ["🔗 URL", "� Batch URLs", "�📄 PDF", "📝 Text"], 
                horizontal=True,
                label_visibility="collapsed"
            )
            
            if "Batch" in input_method:
                # Batch URL mode
                batch_urls = st.text_area(
                    "Enter URLs (one per line)",
                    placeholder="https://example.com/article1\nhttps://youtube.com/watch?v=xyz\nhttps://example.com/article2",
                    height=120
                )
                if st.button("✨ Batch Extract All", type="primary", use_container_width=True):
                    if batch_urls:
                        urls = [u.strip() for u in batch_urls.strip().split('\n') if u.strip()]
                        if urls:
                            st.session_state.batch_urls = urls
                            st.session_state.batch_results = []
                            st.session_state.app_mode = "📋 Batch Summary"
                            st.rerun()
                        
            elif "URL" in input_method:
                url_input = st.text_input("Enter URL (YouTube/Web)", placeholder="https://...")
                if st.button("✨ Extract & Summarize", type="primary", use_container_width=True):
                    if url_input:
                        with st.spinner("Extracting..."):
                            ctype = detect_content_type(url_input)
                            result = extract_content(ctype, url_input)
                            if result.get("success"):
                                st.session_state.extracted_content = result
                                st.session_state.source_url = url_input
                                st.session_state.content_type = ctype
                                st.session_state.redirect_to_summary = True
                                st.rerun()
                            else:
                                st.error(result.get("error"))
                                
            elif "PDF" in input_method:
                uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
                if uploaded_file and st.button("✨ Abstract & Summarize", type="primary", use_container_width=True):
                    with st.spinner("Processing PDF..."):
                        pdf_bytes = uploaded_file.read()
                        result = extract_content("pdf", pdf_bytes, uploaded_file.name)
                        if result.get("success"):
                            st.session_state.extracted_content = result
                            st.session_state.source_url = None
                            st.session_state.content_type = "pdf"
                            st.session_state.redirect_to_summary = True
                            st.rerun()
                        else:
                            st.error(result.get("error"))
                            
            else:
                txt = st.text_area("Paste Text", height=150)
                if txt and st.button("✨ Process Text", type="primary", use_container_width=True):
                    st.session_state.extracted_content = {"text": txt, "success": True}
                    st.session_state.source_url = None
                    st.session_state.content_type = "text"
                    st.session_state.redirect_to_summary = True
                    st.rerun()

    st.divider()
    
    # Quick Access Grid
    st.markdown("### 🧭 Quick Navigation")
    
    def set_mode(mode):
        st.session_state.app_mode = mode

    # Row 1: Core Agents
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("#### 🛡️ Sentinel")
            st.caption("Automated News Watchdog")
            st.button("Open Sentinel", use_container_width=True, on_click=set_mode, args=("🛡️ Sentinel",))

    with c2:
        with st.container(border=True):
            st.markdown("#### 👁️ Autopilot")
            st.caption("Live AI Observer")
            st.button("Open Autopilot", use_container_width=True, on_click=set_mode, args=("👁️ Autopilot",))
                
    with c3:
        with st.container(border=True):
            st.markdown("#### 🕵️‍♂️ Deep Research")
            st.caption("Agentic Web Research")
            st.button("Start Research", use_container_width=True, on_click=set_mode, args=("🕵️‍♂️ Deep Research",))
    
    # Row 2: Content Tools
    c4, c5, c6 = st.columns(3)
    with c4:
        with st.container(border=True):
            st.markdown("#### 📝 Summary")
            st.caption("View Extracted Summaries")
            st.button("Go to Summary", use_container_width=True, on_click=set_mode, args=("📝 Summary",))

    with c5:
        with st.container(border=True):
            st.markdown("#### 💬 Chat")
            st.caption("Q&A with Content")
            st.button("Start Chat", use_container_width=True, on_click=set_mode, args=("💬 Chat",))

    with c6:
        with st.container(border=True):
            st.markdown("#### 🎧 Podcast")
            st.caption("Generate Audio Overview")
            st.button("Podcast Studio", use_container_width=True, on_click=set_mode, args=("🎧 Podcast",))


def generate_conceptual_title(summary: str, summarizer) -> str:
    """
    Use AI to generate a conceptual filename that reflects the core concept.
    """
    if not summary or not summarizer:
        return None
    
    # Use shorter prompt for faster response
    prompt = f"""Task: Create a concise filename (3-8 words) for this content.
Format: Just the title text. No quotes. No extension.
Language: English Only.
Style: Technical, Conceptual.

Summary start:
{summary[:1000]}

Filename:"""

    try:
        # DBG: Check input
        st.sidebar.warning(f"DEBUG: Generating title for summary len={len(summary)}")
        
        # Use non-streaming for reliability
        response = summarizer._generate_response(prompt)
        
        if response.get("success"):
            full_response = response.get("summary", "")
            
            if full_response:
                # Clean up response
                lines = full_response.strip().split('\n')
                
                # Find the best line
                best_title = ""
                for line in lines:
                    clean_line = line.strip().replace('"', '').replace("'", "").replace('`', '')
                    if not clean_line:
                        continue
                        
                    # Remove prefixes
                    lower_line = clean_line.lower()
                    for prefix in ['filename:', 'title:', 'answer:', 'filename', 'here is']:
                        if lower_line.startswith(prefix):
                            clean_line = clean_line[len(prefix):].strip().lstrip(':').strip()
                    
                    if clean_line:
                        best_title = clean_line
                        break
                
                # Final validation
                if best_title and len(best_title) > 2 and len(best_title) < 80:
                    best_title = re.sub(r'[<>:"/\\|?*]', '', best_title)
                    return best_title.strip()
                    
    except Exception as e:
        print(f"Title generation error: {e}")
    
    return None


def extract_title_from_summary(summary: str, source_type: str = None) -> str:
    """Fallback: Extract a meaningful title from summary content"""
    if not summary:
        return None
    
    # Try to find first heading (## or ###)
    heading_match = re.search(r'^##\s*[📋🔑💡📚]?\s*(.+?)$', summary, re.MULTILINE)
    if heading_match:
        title = heading_match.group(1).strip()
        # Remove markdown formatting
        title = re.sub(r'[\[\]\*\#]', '', title)
        if len(title) > 5 and len(title) < 80:
            return title
    
    return None

def render_summary_page(selected_model, language, ctx_size, obsidian_enabled, vault_path, summary_folder, auto_save):
    st.subheader("📋 Summary Content")
    
    # Summary Template Selector
    st.markdown("##### 🎨 Summary Style")
    template_col1, template_col2 = st.columns([2, 3])
    
    with template_col1:
        summary_template = st.selectbox(
            "Template",
            ["📊 Standard", "💼 Executive", "🔧 Technical", "👶 ELI5 (Simple)"],
            label_visibility="collapsed"
        )
    
    with template_col2:
        template_descriptions = {
            "📊 Standard": "Balanced summary with key points",
            "💼 Executive": "Business-focused, decisions & impact",
            "🔧 Technical": "Deep details, code, architecture",
            "👶 ELI5 (Simple)": "Explain Like I'm 5 - simple terms"
        }
        st.caption(template_descriptions.get(summary_template, ""))
            
    # Summarize button
    can_summarize = (
        st.session_state.extracted_content 
        and st.session_state.extracted_content.get("success")
        and selected_model
    )
    
    # Determine content label
    content_type_label = "content"
    if st.session_state.content_type == "youtube":
        content_type_label = "YouTube video transcript"
    elif st.session_state.content_type == "webpage":
        content_type_label = "web article"
    elif st.session_state.content_type == "pdf":
        content_type_label = "PDF document"
    
    if st.button(
        "✨ Generate Summary", 
        type="primary", 
        use_container_width=True,
        disabled=not can_summarize,
    ):
        if can_summarize:
            content = st.session_state.extracted_content.get("text", "")
            
            try:
                summarizer = OllamaSummarizer(
                    model=selected_model, 
                    timeout=300, 
                    num_ctx=ctx_size
                )
                
                # For long content, process in chunks then combine into one summary
                if len(content) > 8000:
                    chunks = summarizer._chunk_content(content, max_chars=6000)
                    st.info(f"📄 Processing {len(chunks)} parts, then combining into one summary...")
                    
                    all_summaries = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    live_preview = st.empty()
                    
                    # Summarize each chunk using STREAMING (never times out)
                    for i, chunk in enumerate(chunks):
                        status_text.markdown(f"🔄 Processing part {i+1}/{len(chunks)}...")
                        
                        # Use streaming to avoid timeout
                        stream_gen = summarizer.summarize(
                            chunk,
                            language=language,
                            content_type=f"{content_type_label} (Part {i+1}/{len(chunks)})",
                            stream=True,  # Streaming never times out!
                        )
                        
                        # Collect streaming response
                        part_text = ""
                        for text_chunk in stream_gen:
                            part_text += text_chunk
                            live_preview.markdown(f"*Part {i+1}:* {part_text[:200]}..." if len(part_text) > 200 else f"*Part {i+1}:* {part_text}")
                        
                        all_summaries.append(part_text)
                        progress_bar.progress((i + 1) / len(chunks))
                    
                    progress_bar.empty()
                    status_text.empty()
                    live_preview.empty()
                    
                    # Combine all summaries into one final summary
                    st.markdown("#### 🤖 Combining into final summary...")
                    combined_content = "\\n\\n---\\n\\n".join(all_summaries)
                    
                    # Final summarization with streaming
                    if language == "th":
                        combine_prompt = f"""[คำสั่ง: จงรวมเนื้อหาสรุปย่อยด้านล่างนี้ ให้เป็น 'สรุปฉบับสมบูรณ์' ที่มีความละเอียดและครอบคลุมที่สุด]

กฎการรวมเนื้อหา:
1. ห้ามตัดทอนรายละเอียดสำคัญ: ต้องเก็บข้อมูล ตัวเลข ชื่อเฉพาะ และบริบททั้งหมดไว้
2. เรียบเรียงใหม่ให้ต่อเนื่อง: ไม่ใช่แค่เอามาต่อกัน แต่ต้องร้อยเรียงให้อ่านลื่นไหลเป็นเรื่องเดียวกัน
3. จัดหมวดหมู่ใหม่: แบ่งหัวข้อหลัก หัวข้อย่อย ให้ชัดเจนตามเนื้อหา
4. ความยาว: ไม่จำกัดความยาว เน้นความครบถ้วนสมบูรณ์เหมือนต้นฉบับ
5. ใช้ภาษาไทยเป็นหลัก (ทับศัพท์ได้เท่าที่จำเป็น)
6. ใช้ Emoji ตกแต่งให้น่าอ่านโดยไม่มากเกินไปใช้เฉพาะหัวข้อใหญ่หรือใช้ส่วนที่อยากให้เห็นความแตกต่างหรือเน้นย้ำส่วนนั้นๆ

เนื้อหาที่ต้องรวม:
{combined_content}

[เริ่มเขียนสรุปฉบับสมบูรณ์:]"""
                    else:
                        combine_prompt = f"""[Instruction: Combine the following partial summaries into a single, comprehensive Master Summary.]

Rules:
1. Do NOT lose details: Keep all key figures, names, and context.
2. Cohesion: Rewrite to ensure smooth flow, not just concatenation.
3. Structure: Re-organize into logical Main Topics and Sub-points.
4. Comprehensive: Prioritize completeness over brevity.

Content to combine:
{combined_content}

[Begin Master Summary:]"""
                    
                    stream_generator = summarizer._stream_response(combine_prompt)
                    summary_placeholder = st.empty()
                    full_response = ""
                    
                    for text_chunk in stream_generator:
                        full_response += text_chunk
                        summary_placeholder.markdown(full_response + "▌")
                    
                    summary_placeholder.markdown(full_response)
                else:
                    # Single chunk - stream directly
                    st.markdown("#### 🤖 Generating Summary...")
                    
                    # Convert template display name to code name
                    template_map = {
                        "📊 Standard": "standard",
                        "💼 Executive": "executive",
                        "🔧 Technical": "technical",
                        "👶 ELI5 (Simple)": "eli5"
                    }
                    template_code = template_map.get(summary_template, "standard")
                    
                    stream_generator = summarizer.summarize(
                        content,
                        language=language,
                        content_type=content_type_label,
                        stream=True,
                        template=template_code,
                    )
                    
                    summary_placeholder = st.empty()
                    full_response = ""
                    
                    for chunk in stream_generator:
                        full_response += chunk
                        summary_placeholder.markdown(full_response + "▌")
                    
                    summary_placeholder.markdown(full_response)
                
                result = {
                    "summary": full_response,
                    "model": selected_model,
                    "success": True,
                }
                st.session_state.summary_result = result
                st.success("✅ Summary complete!")
                
                # Auto-save to Obsidian
                if obsidian_enabled and auto_save and vault_path and result.get("success"):
                    with st.spinner("📝 Generating filename..."):
                        # Try AI-generated conceptual title first
                        auto_title = generate_conceptual_title(
                            result.get("summary", ""),
                            summarizer
                        )
                        # Fallback to simple extraction
                        if not auto_title:
                            auto_title = extract_title_from_summary(
                                result.get("summary", ""),
                                st.session_state.content_type
                            )
                    
                    obsidian = ObsidianIntegration(vault_path, summary_folder)
                    save_result = obsidian.save_summary(
                        summary=result.get("summary", ""),
                        title=auto_title,  # Use AI-generated title
                        source_url=st.session_state.source_url,
                        source_type=st.session_state.content_type,
                        language=language,
                    )
                    if save_result.get("success"):
                        st.toast(f"✅ Saved to Obsidian: {save_result.get('filename')}")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display summary
    if st.session_state.summary_result:
        result = st.session_state.summary_result
        
        if result.get("success"):
            st.markdown(result.get("summary", ""))
            
            # Action buttons
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.download_button(
                    "📥 Download Summary",
                    data=result.get("summary", ""),
                    file_name="summary.md",
                    mime="text/markdown",
                )
            
            with col_b:
                # Manual save to Obsidian
                if obsidian_enabled and vault_path:
                    if st.button("📝 Save to Obsidian"):
                        obsidian = ObsidianIntegration(vault_path, summary_folder)
                        save_result = obsidian.save_summary(
                            summary=result.get("summary", ""),
                            source_url=st.session_state.source_url,
                            source_type=st.session_state.content_type,
                            language=language,
                        )
                        if save_result.get("success"):
                            st.success(f"✅ Saved: {save_result.get('filename')}")
                        else:
                            st.error(f"❌ {save_result.get('error')}")
                else:
                    if st.button("📋 Copy to Clipboard"):
                        st.code(result.get("summary", ""), language=None)
                        st.info("Select and copy the text above")
            
            st.caption(f"🤖 Model: {result.get('model', 'unknown')}")
        else:
            st.error(f"❌ {result.get('error', 'Failed to generate summary')}")
    
    elif not can_summarize:
        if not selected_model:
            st.warning("⚠️ Please ensure Ollama is running with a model installed")
        else:
            st.info("👆 Extract content first, then generate summary")

def render_chat_page(selected_model, ctx_size):
    st.subheader("💬 AI Chat Assistant")
    st.caption("🧠 **Memory enabled** - I remember our conversation!")
    
    # Initialize LangChain chat (with memory)
    from summarizer.langchain_chat import LangChainChat
    
    if "langchain_chat" not in st.session_state:
        st.session_state.langchain_chat = LangChainChat(
            model=selected_model or "llama3.1",
            memory_window=10,
            num_ctx=ctx_size
        )
    
    chat_instance = st.session_state.langchain_chat
    
    # Update model if changed
    if chat_instance.model_name != selected_model:
        chat_instance.set_model(selected_model, ctx_size)
    
    # Sidebar controls for chat
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🗑️ Clear Chat"):
            chat_instance.clear_memory()
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        st.caption(chat_instance.get_memory_summary())
    
    # Context handling
    has_content = st.session_state.extracted_content and st.session_state.extracted_content.get("success")
    
    with col3:
        if has_content:
            if st.button("📄 Clear Context"):
                chat_instance.clear_context()
                st.session_state.extracted_content = None
                st.rerun()
    
    if has_content:
        content_text = st.session_state.extracted_content.get("text", "")
        chat_instance.set_context(content_text)
        st.success(f"📄 Context loaded ({len(content_text):,} chars)")
    else:
        chat_instance.clear_context()
        
        # Unified RAG toggle - search Library for context
        use_library_rag = st.checkbox(
            "📚 Enable Library RAG",
            value=False,
            help="Automatically search your Library for relevant context"
        )
        
        if use_library_rag:
            st.info("💡 I'll search your Library for relevant info when you ask questions!")
        else:
            st.info("💡 Extract content from URL/PDF to include as context, or just ask anything!")
    
    st.divider()
    
    # Display chat messages from history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask anything..."):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # If Library RAG is enabled and no other context, search Library
                if not has_content and 'use_library_rag' in dir() and use_library_rag:
                    try:
                        # Search library for context
                        vector_store = VectorStore()
                        library_results = vector_store.search(prompt, top_k=3)
                        
                        if library_results:
                            library_context = "\n\n".join([
                                f"📚 From '{r.get('title', 'Unknown')}'\n{r.get('text', '')[:500]}"
                                for r in library_results
                            ])
                            chat_instance.set_context(f"Relevant context from your Library:\n\n{library_context}")
                            message_placeholder.markdown("*🔍 Found relevant context in your Library...*")
                    except Exception as lib_err:
                        pass  # Continue without library context
                
                # Stream response with LangChain (memory handled internally)
                stream_gen = chat_instance.chat(message=prompt, stream=True)
                
                for chunk in stream_gen:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                
                # Add assistant response to UI history
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                message_placeholder.markdown(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

def render_podcast_page(selected_model, ctx_size):
    st.subheader("🎧 Podcast Generator (Thai)")
    st.markdown("Convert your summary into a 2-person dialogue (Host A & Host B) to listen on the go.")
    
    # Check if summary exists
    if not st.session_state.summary_result or not st.session_state.summary_result.get("success"):
        st.info("👆 Please generate a summary first (in 'Summary' tab) to create a podcast.")
    else:
        result = st.session_state.summary_result
        summary_text = result.get("summary", "")
        
        # Initialize state for podcast
        if "podcast_audio_path" not in st.session_state:
                st.session_state.podcast_audio_path = None
        if "podcast_script" not in st.session_state:
                st.session_state.podcast_script = None

        st.markdown("#### 🎧 Generate Podcast")
        
        # --- Voice Library / Customization ---
        with st.expander("🎙️ Voice Customization (XTTS v2)", expanded=False):
            st.info("Upload reference audio files to clone voices (XTTS only).")
            
            # 1. Upload New Voice
            st.markdown("##### 📤 Upload New Voice")
            col_up1, col_up2 = st.columns([3, 1])
            with col_up1:
                uploaded_voice = st.file_uploader("Upload Audio (WAV/MP3)", type=["wav", "mp3"])
                voice_name_input = st.text_input("Name this voice (e.g. 'Narrator', 'Boss')", placeholder="MyVoice")
            
            with col_up2:
                st.write("") # Spacer
                st.write("")
                if st.button("💾 Save Voice", type="primary", use_container_width=True):
                    if uploaded_voice and voice_name_input:
                        # Ensure filename safe
                        safe_name = "".join([c for c in voice_name_input if c.isalnum() or c in (' ', '_', '-')]).strip()
                        if not safe_name: safe_name = "Unnamed_Voice"
                        
                        save_path = f"voices/{safe_name}.wav"
                        
                        # Save file
                        try:
                            if not os.path.exists("voices"): os.makedirs("voices")
                            
                            # Convert to correct WAV format using dry run? No, just save.
                            # XTTS handles most formats if we convert to WAV using pydub
                            with open(save_path, "wb") as f:
                                f.write(uploaded_voice.getbuffer())
                            
                            st.success(f"✅ Saved '{safe_name}'!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving: {e}")
                    else:
                        st.warning("Please upload file AND provide a name.")

            st.divider()
            
            # 2. Manage / Select Voices
            st.markdown("##### 🎭 Assign Voices")
            
            # Get list of voices
            if not os.path.exists("voices"): os.makedirs("voices")
            available_voices = [f for f in os.listdir("voices") if f.endswith(".wav")]
            # Sort: put refs first if exist
            available_voices.sort()
            
            if not available_voices:
                st.warning("No voices found. Please upload one!")
                voice_options = ["Default (Amy)", "Default (Ryan)"]
            else:
                voice_options = available_voices
                
            c_host_a, c_host_b = st.columns(2)
            
            with c_host_a:
                st.markdown("**Host A (Female/Main)**")
                # Try to find 'female_ref.wav' or 'Achara' as default
                default_idx_a = 0
                for i, v in enumerate(voice_options):
                    if "female" in v.lower() or "prem" in v.lower() or "amy" in v.lower():
                        default_idx_a = i
                        break
                        
                sel_voice_a = st.selectbox("Select Voice for A", voice_options, index=default_idx_a, key="voice_sel_a")
                
                # Preview
                if sel_voice_a in available_voices:
                     st.audio(f"voices/{sel_voice_a}")

            with c_host_b:
                st.markdown("**Host B (Male/Guest)**")
                # Try to find 'male_ref.wav' or 'Niwat' as default
                default_idx_b = 0
                for i, v in enumerate(voice_options):
                    if "male" in v.lower() or "niwat" in v.lower() or "ryan" in v.lower():
                        default_idx_b = i
                        break

                sel_voice_b = st.selectbox("Select Voice for B", voice_options, index=default_idx_b, key="voice_sel_b")
                
                # Preview
                if sel_voice_b in available_voices:
                     st.audio(f"voices/{sel_voice_b}")
            
            # Store selections in session state to pass to generator
            if sel_voice_a in available_voices:
                st.session_state['host_a_path'] = os.path.abspath(f"voices/{sel_voice_a}")
            if sel_voice_b in available_voices:
                st.session_state['host_b_path'] = os.path.abspath(f"voices/{sel_voice_b}")

        st.info("Click below to create a script and audio automatically.")
        
        # Style Configuration
        STYLES = [
            {
                "id": "regular",
                "name": "🥰 Friendly Chat",
                "desc": "Casual, energetic conversation. Hosts agree and explain concepts.",
                "sample": [{"speaker": "A", "text": "สวัสดีค่ะ วันนี้เรามาคุยกันแบบสบายๆ นะคะ"}, {"speaker": "B", "text": "ใช่ครับ ผมพร้อมแลกเปลี่ยนความเห็นเต็มที่ครับ"}]
            },
            {
                "id": "debate",
                "name": "🥊 Debate Mode",
                "desc": "Heated argument. Host B (Skeptic) challenges every point Host A makes.",
                "sample": [{"speaker": "A", "text": "ผมว่าเรื่องนี้มันยอดเยี่ยมมากเลยนะ!"}, {"speaker": "B", "text": "เดี๋ยวก่อนครับ... ผมว่าคุณกำลังมองข้ามปัญหาใหญ่นะ"}]
            },
            {
                "id": "news",
                "name": "📰 News Anchor",
                "desc": "Formal, fast-paced breaking news. Anchor and Field Reporter.",
                "sample": [{"speaker": "A", "text": "สวัสดีค่ะ ข่าวต้นชั่วโมงวันนี้..."}, {"speaker": "B", "text": "รายงานจากพื้นที่ครับ สถานการณ์กำลังเข้มข้น"}]
            },
            {
                "id": "story",
                "name": "📖 Storyteller",
                "desc": "Slow, emotional documentary style. ‘Once upon a time’ vibe.",
                "sample": [{"speaker": "A", "text": "กาลครั้งหนึ่ง... ในดินแดนที่ห่างไกล..."}, {"speaker": "B", "text": "และนั่นคือบทเรียนที่สำคัญที่สุด..."}]
            }
        ]
        
        # Render Gallery
        st.write("Select Voice Style:")
        
        selected_style_name = st.radio(
            "Choose Style:",
            [s["name"] for s in STYLES],
            label_visibility="collapsed"
        )
        
        # Find selected style object
        current_style = next(s for s in STYLES if s["name"] == selected_style_name)
        style_code = current_style["id"]
        
        st.info(f"**{current_style['name']}**: {current_style['desc']}")
        
        # Preview Button for the SELECTED style
        if st.button(f"🔊 Listen to Sample ({current_style['name']})"):
                with st.spinner("Generating sample..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_prev:
                        prev_path = tmp_prev.name
                    try:
                        prev_gen = PodcastGenerator()
                        success, _ = asyncio.run(prev_gen.generate_audio(current_style["sample"], prev_path))
                        if success:
                            st.audio(prev_path, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()

        # Single Button for Auto-Generation
        if st.button("🎙️ Generate Podcast (Auto)", type="primary", help="Generate Script + Audio in one click"):
            with st.spinner(f"✍️ Writing script ({style_code} mode)..."):
                pod_gen = PodcastGenerator(summarizer=OllamaSummarizer(model=selected_model, num_ctx=ctx_size))
                script, error_msg = pod_gen.generate_script(summary_text, language="th", style=style_code)
                
                if script:
                    st.session_state.podcast_script = script
                    st.success(f"✅ Script generated! ({len(script)} lines)")
                    
                    # Auto-chain: Generate Audio immediately
                    st.warning("⚠️ Note: If using XTTS v2, the first run will take ~5-10 mins to download the model (2GB). Please wait.")
                    with st.spinner(f"🗣️ Synthesizing audio (XTTS v2)..."):
                        # Create temp path
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                            output_path = tmp_file.name
                        
                        try:
                            # Use selected voices from session state
                            voice_a = st.session_state.get('host_a_path')
                            voice_b = st.session_state.get('host_b_path')
                            success, audio_err = pod_gen.generate_audio(script, output_path, voice_a_path=voice_a, voice_b_path=voice_b)
                            
                            if success:
                                st.session_state.podcast_audio_path = output_path
                                st.success("✅ Audio Ready!")
                            else:
                                st.error(f"❌ Audio generation failed: {audio_err}")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    # Handle errors
                    if error_msg and ("exit status 2" in str(error_msg) or "500" in str(error_msg)):
                        st.error("❌ Ollama OOM. Try reducing Context Size.")
                    else:
                        st.error(f"❌ Failed: {error_msg}")

        # Display Audio Player (Priority)
        if st.session_state.podcast_audio_path and os.path.exists(st.session_state.podcast_audio_path):
            st.divider()
            st.markdown("#### 📻 Now Playing")
            st.audio(st.session_state.podcast_audio_path, format="audio/mp3")
            
            # Download button
            with open(st.session_state.podcast_audio_path, "rb") as f:
                audio_bytes = f.read()
                st.download_button(
                    label="📥 Download MP3",
                    data=audio_bytes,
                    file_name=f"podcast_summary.mp3",
                    mime="audio/mpeg",
                    use_container_width=True
                )

        # Script Editor (Below Audio)
        if st.session_state.podcast_script:
            with st.expander("📝 Edit Script & Regenerate", expanded=False):
                st.info("💡 You can edit the text below and click 'Regenerate' to fix any pronunciation or wording.")
                
                # Editable Table
                edited_script = st.data_editor(
                    st.session_state.podcast_script,
                    column_config={
                        "speaker": st.column_config.SelectboxColumn("Speaker", options=["A", "B"], width="small"),
                        "text": st.column_config.TextColumn("Dialogue", width="large"),
                    },
                    use_container_width=True,
                    num_rows="dynamic"
                )
                
                if st.button("🔄 Regenerate Audio from Edit"):
                    with st.spinner(f"🗣️ Re-synthesizing {len(edited_script)} lines..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                            output_path = tmp_file.name
                        
                        try:
                            pod_gen = PodcastGenerator()
                            success, audio_err = asyncio.run(pod_gen.generate_audio(edited_script, output_path))
                            
                            if success:
                                st.session_state.podcast_audio_path = output_path
                                st.experimental_rerun()
                            else:
                                st.error(f"❌ Audio generation failed: {audio_err}")
                        except Exception as e:
                            st.error(f"Error: {e}")

def render_sentinel(sentinel_agent, selected_model):
    st.header("🛡️ The Content Sentinel")
    st.caption("Automated Watchdog for YouTube & Websites")
    
    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.subheader("📡 Source Manager")
        
        # Add New Source
        # Add New Source
        with st.expander("➕ Add New Source", expanded=False):
            new_src_name = st.text_input("Source Name", placeholder="e.g. TechCrunch")
            new_src_url = st.text_input("RSS / Channel URL", placeholder="https://...")
            new_src_type = st.selectbox("Type", ["rss", "youtube"])
            
            if st.button("Add Source"):
                if new_src_name and new_src_url:
                    sentinel_agent.add_source(new_src_name, new_src_url, new_src_type)
                    st.success(f"Added {new_src_name}")
                    st.rerun()
                else:
                    st.error("Name and URL required.")
        
        # List Sources
        sources = sentinel_agent.sources
        if not sources:
            st.info("No sources configured.")
        else:
            with st.expander(f"📚 Active Sources ({len(sources)})", expanded=False):
                for i, src in enumerate(sources):
                    with st.expander(f"📝 {src['name']}", expanded=False):
                        # Edit Form
                        edit_name = st.text_input("Name", value=src['name'], key=f"s_name_{i}")
                        edit_url = st.text_input("URL", value=src['url'], key=f"s_url_{i}")
                        edit_type = st.selectbox("Type", ["rss", "youtube"], index=0 if src['type']=="rss" else 1, key=f"s_type_{i}")
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            if st.button("💾 Save", key=f"s_save_{i}"):
                                sentinel_agent.update_source(src['url'], edit_name, edit_url, edit_type)
                                st.success("Updated!")
                                st.rerun()
                        with col_e2:
                            if st.button("🗑️ Delete", key=f"s_del_{i}"):
                                    sentinel_agent.remove_source(src['url'])
                                    st.rerun()
                        
                        st.caption(f"Last Check: {src.get('last_checked', 'Never')}")
        
        # Scheduled Scans Section
        st.markdown("### ⏰ Scheduled Scans")
        with st.expander("Configure Auto-Scan", expanded=False):
            # Initialize schedule state
            if "sentinel_schedule" not in st.session_state:
                st.session_state.sentinel_schedule = {
                    "enabled": False,
                    "interval": "daily",
                    "last_scan": None,
                    "next_scan": None
                }
            
            schedule = st.session_state.sentinel_schedule
            
            schedule_enabled = st.toggle(
                "Enable Auto-Scan",
                value=schedule.get("enabled", False),
                help="Automatically scan sources on a schedule"
            )
            
            if schedule_enabled:
                options = ["Every 30 minutes", "Hourly", "Every 6 hours", "Daily"]
                current_val = schedule.get("interval", "Daily")
                
                # Robust index finding (case-insensitive fallback)
                try:
                    default_index = options.index(current_val)
                except ValueError:
                    # Try finding match ignoring case
                    default_index = 3 # Default to Daily
                    for i, opt in enumerate(options):
                        if opt.lower() == current_val.lower():
                            default_index = i
                            break
                
                schedule_interval = st.selectbox(
                    "Scan Interval",
                    options,
                    index=default_index
                )
                
                # Update schedule state
                st.session_state.sentinel_schedule["enabled"] = True
                st.session_state.sentinel_schedule["interval"] = schedule_interval
                
                # Calculate next scan time
                import datetime
                now = datetime.datetime.now()
                interval_map = {
                    "Every 30 minutes": datetime.timedelta(minutes=30),
                    "Hourly": datetime.timedelta(hours=1),
                    "Every 6 hours": datetime.timedelta(hours=6),
                    "Daily": datetime.timedelta(days=1)
                }
                
                last_scan = schedule.get("last_scan")
                if last_scan:
                    next_scan = last_scan + interval_map[schedule_interval]
                    st.session_state.sentinel_schedule["next_scan"] = next_scan
                    
                    st.info(f"⏰ **Last scan**: {last_scan.strftime('%Y-%m-%d %H:%M')}")
                    st.info(f"📅 **Next scan**: {next_scan.strftime('%Y-%m-%d %H:%M')}")
                    
                    # Check if scan is due
                    if now >= next_scan:
                        st.success("🔔 Scan is due! Click 'Scan Now' or it will run automatically.")
                else:
                    st.caption("No previous scan. Click 'Scan Now' to start.")
                
                # Manual trigger with schedule update
                if st.button("🔍 Scan Now & Update Schedule"):
                    st.session_state.sentinel_schedule["last_scan"] = now
                    st.rerun()
            else:
                st.session_state.sentinel_schedule["enabled"] = False
                st.caption("Enable to set up automatic scanning.")
    
    with col_s2:
        st.subheader("🚀 Mission Control")
        
        # Configuration
        vault_path = st.text_input("📂 Obsidian Vault Path (Optional)", 
                                 placeholder="e.g. C:/Users/PP/Documents/Obsidian/Inbox",
                                 help="If set, summaries and audio will be pushed specifically to this folder.")
        
        # Step 1: Scan Button
        if st.button("🔍 Scan for New Updates", type="primary"):
            if not sources:
                st.warning("Please add sources first.")
            else:
                with st.spinner("Scanning feeds..."):
                     candidates = sentinel_agent.scan_for_updates()
                     if candidates:
                         st.session_state.sentinel_candidates = candidates
                         st.success(f"Found {len(candidates)} new updates!")
                         st.rerun()
                     else:
                         st.info("No new updates found.")

        # Step 2: Review & Process
        if "sentinel_candidates" in st.session_state and st.session_state.sentinel_candidates:
            st.divider()
            st.subheader(f"📋 Review Queue ({len(st.session_state.sentinel_candidates)})")
            
            # Selection UI
            # Group by Source for better display
            
            # Split candidates into lists
            news_items = [x for x in st.session_state.sentinel_candidates if x.get('source_category') != 'paper']
            paper_items = [x for x in st.session_state.sentinel_candidates if x.get('source_category') == 'paper']
            
            # Initialize selection state if needed (moved to top to avoid AttributeError)
            if "sentinel_selection" not in st.session_state:
                st.session_state.sentinel_selection = {}
            
            # Create Tabs
            tab_news, tab_papers = st.tabs([f"🗞️ News Hub ({len(news_items)})", f"🎓 Research Papers ({len(paper_items)})"])
            
            # --- Tab 1: NEWS ---
            with tab_news:
                # Group by Source
                news_candidates = sorted(news_items, key=lambda x: x['source_name'])
                
                with st.form("sentinel_form_news"):
                    # Quick Select
                    c1, c2 = st.columns(2)
                    sel_all_news = c1.form_submit_button("✅ Select All News")
                    clr_all_news = c2.form_submit_button("⬜ Clear News")
                    
                    if sel_all_news:
                        for item in news_candidates: st.session_state.sentinel_selection[f"check_{item['uid']}"] = True
                    elif clr_all_news:
                         for item in news_candidates: st.session_state.sentinel_selection[f"check_{item['uid']}"] = False
                    
                    for source_name, group in groupby(news_candidates, key=lambda x: x['source_name']):
                        st.markdown(f"#### 📺 {source_name}")
                        for item in group:
                            # Use UID for key to avoid index clashes between tabs
                            key = f"check_{item['uid']}"
                            default_val = st.session_state.sentinel_selection.get(key, False)
                            
                            c_check, c_content = st.columns([0.05, 0.95])
                            with c_check:
                                is_checked = st.checkbox("Select", value=default_val, key=key, label_visibility="collapsed")
                                st.session_state.sentinel_selection[key] = is_checked
                            with c_content:
                                st.markdown(f"**{item['title']}**")
                                st.caption(f"{item['published']}")
                        st.divider()
                        
                    if st.form_submit_button("🚀 Process Selected News", type="primary"):
                        # Gather all checked
                        items_to_process = [x for x in st.session_state.sentinel_candidates if st.session_state.sentinel_selection.get(f"check_{x['uid']}", False)]
                        if items_to_process:
                             st.session_state.sentinel_processing_queue = items_to_process
                             st.session_state.sentinel_candidates = [] 
                             st.rerun()
                        else:
                            st.warning("No items selected.")

            # --- Tab 2: PAPERS ---
            with tab_papers:
                paper_candidates = sorted(paper_items, key=lambda x: x['source_name'])
                
                with st.form("sentinel_form_papers"):
                    # Quick Select
                    c1, c2 = st.columns(2)
                    sel_all_papers = c1.form_submit_button("✅ Select All Papers")
                    clr_all_papers = c2.form_submit_button("⬜ Clear Papers")

                    if sel_all_papers:
                        for item in paper_candidates: st.session_state.sentinel_selection[f"check_{item['uid']}"] = True
                    elif clr_all_papers:
                         for item in paper_candidates: st.session_state.sentinel_selection[f"check_{item['uid']}"] = False

                    if not paper_candidates:
                        st.info("No new papers found today.")
                    
                    for source_name, group in groupby(paper_candidates, key=lambda x: x['source_name']):
                        st.markdown(f"#### 📜 {source_name}")
                        for item in group:
                            key = f"check_{item['uid']}"
                            default_val = st.session_state.sentinel_selection.get(key, False)
                            
                            c_check, c_content = st.columns([0.05, 0.95])
                            with c_check:
                                is_checked = st.checkbox("Select", value=default_val, key=key, label_visibility="collapsed")
                                st.session_state.sentinel_selection[key] = is_checked
                            with c_content:
                                st.markdown(f"**{item['title']}**")
                                st.caption(f"📄 {item['published']}")
                        st.divider()

                    if st.form_submit_button("🚀 Process Selected Papers", type="primary"):
                        items_to_process = [x for x in st.session_state.sentinel_candidates if st.session_state.sentinel_selection.get(f"check_{x['uid']}", False)]
                        if items_to_process:
                             st.session_state.sentinel_processing_queue = items_to_process
                             st.session_state.sentinel_candidates = [] 
                             st.rerun()
                        else:
                            st.warning("No items selected.")

        # Step 3: Execution Output
        if "sentinel_processing_queue" in st.session_state and st.session_state.sentinel_processing_queue:
             st.divider()
             st.subheader("⚙️ Processing...")
             
             sentinel_status = st.status("Log", expanded=True)
             feed_container = st.container()
             
             async def run_batch():
                 agent = sentinel_agent
                 agent.summarizer = OllamaSummarizer(model=selected_model) 
                 agent.podcaster = PodcastGenerator(summarizer=agent.summarizer)
                 
                 for item in st.session_state.sentinel_processing_queue:
                     async for update in agent.process_item(item, vault_path=vault_path):
                        if isinstance(update, dict):
                            msg_type = update.get("type", "log")
                            if msg_type == "log":
                                sentinel_status.write(update["message"])
                            elif msg_type == "item":
                                # Render Card
                                with feed_container.container(border=True):
                                    c1, c2 = st.columns([3, 1])
                                    with c1:
                                        st.markdown(f"### {update['title']}")
                                        st.caption(f"Source: {update['source']} • {update['date']}")
                                        st.write(update['summary'])
                                        st.markdown(f"**[🔗 Watch Video / Read Article]({update['link']})**")
                                    with c2:
                                        if update.get('audio_path'):
                                            st.audio(update['audio_path'])
                                            st.caption("🎧 Audio Summary")
                 
                 sentinel_status.update(label="✅ Batch Complete!", state="complete", expanded=False)
             
             asyncio.run(run_batch())
             
             # Clear queue after done
             st.session_state.sentinel_processing_queue = []
             st.success("All selected items processed!")

def render_autopilot(observer_agent, selected_model):
    st.header("👁️ Autopilot Observer")
    st.markdown("*Your AI Watchdog looking for breaking updates.*")
    
    # Initialize Observer if needed (or update model)
    # Passed agent should theoretically be initialized, but we update model here
    observer_agent.model_name = selected_model or "llama3.1"
    observer_agent.summarizer = OllamaSummarizer(model=selected_model or "llama3.1")

    # Layout: Stacked vertically to avoid cramping in the 50% width column
    st.subheader("🚀 Mission Control")
    
    # Mission Control Section
    col_ctrl_1, col_ctrl_2 = st.columns([2, 1])
    with col_ctrl_1:
        if st.button("🔄 Run Autopilot Cycle", type="primary", use_container_width=True):
            log_container = st.container(height=300, border=True)
            results_container = st.container()
            
            watchlist_items = observer_agent.get_watchlist()
            if not watchlist_items:
                log_container.warning("Watchlist is empty. Add topics first.")
            else:
                progress_bar = log_container.progress(0)
                
                for i, item in enumerate(watchlist_items):
                    topic = item['topic']
                    log_container.markdown(f"**Scanning: `{topic}`...**")
                    
                    # 1. Scan & Curate Top 5
                    digest = observer_agent.scan_topic(item)
                    
                    if digest.get("error"):
                         log_container.error(f"Error for {topic}: {digest['error']}")
                         observer_agent.update_topic_status(topic, "Error")
                    else:
                         top_news = digest.get("top_news", [])
                         count = len(top_news)
                         log_container.success(f"  > Found {count} relevant updates.")
                         observer_agent.update_topic_status(topic, f"Updated ({count} items)")
                         
                         # Display Result Card
                         with results_container.container(border=True):
                             st.markdown(f"### 📰 {topic}: Top Updates")
                             st.caption(f"Last Updated: {datetime.datetime.now().strftime('%H:%M')}")
                             
                             if not top_news:
                                 st.info("No significant news found today.")
                             else:
                                 for news in top_news:
                                     st.markdown(f"**{news.get('title', 'Untitled')}**")
                                     st.write(news.get('summary', ''))
                                     # Formatting Source link
                                     url = news.get("url", "#")
                                     date = news.get("date", "")
                                     st.markdown(f"[🔗 Source ({date})]({url})")
                                     st.divider()

                    progress_bar.progress((i + 1) / len(watchlist_items))
                
                log_container.success("News Digest Complete.")

    st.divider()
    
    st.subheader("📡 Watchlist Management")
    
    # Add Topic Section
    col_add_1, col_add_2 = st.columns([3, 1])
    with col_add_1:
         new_topic = st.text_input("New Topic", placeholder="e.g. NVIDIA Stock, Thailand Politics...", label_visibility="collapsed")
    with col_add_2:
         if st.button("Add Topic", use_container_width=True):
            if new_topic:
                if observer_agent.add_topic(new_topic):
                    st.success(f"Added '{new_topic}'")
                    observer_agent.watchlist = observer_agent._load_watchlist() 
                    st.rerun()
                else:
                    st.warning("Topic exists.")
    
    # Add GitHub Trending Button
    if st.button("📈 Add 'GitHub Top Trending'", use_container_width=True):
        if observer_agent.add_topic("GitHub Top Trending", source_type="github_trending"):
            st.success("Added GitHub Trending!")
            observer_agent.watchlist = observer_agent._load_watchlist() 
            st.rerun()
        else:
            st.warning("Already in watchlist.")

    # Display Watchlist Items
    watchlist_items = observer_agent.get_watchlist()
    
    if not watchlist_items:
        st.info("Watchlist is empty.")
    else:
        # Grid layout for items if possible, or just vertical list
        for idx, item in enumerate(watchlist_items):
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 2, 1])
                with c1:
                    st.markdown(f"**{item['topic']}**")
                with c2:
                    st.caption(f"{item['last_status']}")
                with c3:
                    if st.button("🗑️", key=f"del_{idx}"):
                        observer_agent.remove_topic(item['topic'])
                        st.rerun()

def render_deep_research(selected_model, language, ctx_size):
    st.subheader("🕵️‍♂️ Deep Research Agent")
    st.markdown("Generates a comprehensive report by searching and synthesizing multiple sources.")
    
    # State Persistence for Inputs
    if "research_topic" not in st.session_state:
        st.session_state.research_topic = ""

    topic_input = st.text_input("Enter Topic", 
                               value=st.session_state.research_topic,
                               placeholder="e.g. Future of Solid State Batteries",
                               key="dr_topic_input")
    
    # Update state on change (manual sync if needed, or rely on key, but let's be safe)
    st.session_state.research_topic = topic_input

    # Config Section
    col_cfg1, col_cfg2 = st.columns([1, 1])
    with col_cfg1:
        max_sources = st.slider("Number of Sources", min_value=3, max_value=10, value=5)
    with col_cfg2:
        use_advanced_agent = st.checkbox(
            "🤖 Advanced Agent Mode", 
            value=False,
            help="Uses LangChain ReAct agent with arXiv & HackerNews (slower but more thorough)"
        )

    def start_research_callback():
        st.session_state.is_processing = True
        st.session_state.research_report = "" # Clear previous
        st.session_state.research_error = None # Clear errors

    # Triggers
    col_btn, col_new = st.columns([1, 4])
    with col_btn:
        start_btn = st.button("🚀 Start Deep Research", 
                            type="primary", 
                            disabled=not topic_input or st.session_state.is_processing,
                            on_click=start_research_callback)
    
    with col_new:
         if st.session_state.research_report and not st.session_state.is_processing:
             if st.button("🔄 New Search"):
                 st.session_state.research_report = ""
                 st.session_state.research_error = None
                 st.rerun()

    # Output Container
    output_container = st.container()

    # Display Error if exists (Persistent)
    if st.session_state.research_error:
        st.error(st.session_state.research_error)
        if st.button("Dismiss Error"):
            st.session_state.research_error = None
            st.rerun()
    
    # --- PROCESSING BLOCK ---
    if st.session_state.is_processing:
        with output_container:
            status_text = st.status("🕵️‍♂️ Researching...", expanded=True)
            report_placeholder = st.empty()
            
            try:
                if not selected_model:
                     st.error("Please select a model first.")
                     st.session_state.is_processing = False
                     st.rerun()
                
                full_report_text = ""
                has_content = False
                
                if use_advanced_agent:
                    # LangChain ReAct Agent with multiple tools
                    from agents.langchain_research_agent import LangChainResearchAgent
                    
                    status_text.write("🤖 Using Advanced LangChain Agent...")
                    status_text.write("🔧 Tools: Web Search, arXiv, HackerNews")
                    
                    lc_agent = LangChainResearchAgent(model=selected_model, num_ctx=ctx_size)
                    result = lc_agent.research_stream(st.session_state.research_topic)
                    
                    if result.get("success"):
                        # Show steps taken
                        for step in result.get("steps", []):
                            status_text.write(f"🔍 Used **{step['tool']}**: {step['input'][:50]}...")
                        
                        full_report_text = result.get("report", "")
                        has_content = bool(full_report_text)
                        report_placeholder.markdown(full_report_text)
                        status_text.update(label="✅ Research Complete!", state="complete", expanded=False)
                    else:
                        st.session_state.research_error = result.get("error", "Unknown error")
                else:
                    # Original streaming agent
                    agent = ResearchAgent(summarizer=OllamaSummarizer(model=selected_model, num_ctx=ctx_size))
                    
                    # Run the generator
                    search_gen = agent.research_topic(st.session_state.research_topic, max_sources=max_sources, language=language)
                
                    for update in search_gen:
                        if isinstance(update, str):
                            status_text.write(update)
                        elif isinstance(update, dict):
                            if update["type"] == "chunk":
                                full_report_text += update["content"]
                                report_placeholder.markdown(full_report_text + "▌")
                                has_content = True
                            elif update["type"] == "complete":
                                status_text.update(label="✅ Research Complete!", state="complete", expanded=False)
                                has_content = True
                
                # Finalize
                if has_content and full_report_text:
                    st.session_state.research_report = full_report_text
                else:
                    # If we got here with no content, it means no results found or early exit
                    st.session_state.research_error = "❌ No research results found. Try a different topic."
                
            except Exception as e:
                st.session_state.research_error = f"❌ An error occurred: {str(e)}"
            finally:
                # Always reset busy state
                st.session_state.is_processing = False
                st.rerun()

    # --- DISPLAY BLOCK (Persistent) ---
    elif st.session_state.research_report:
        with output_container:
            st.success("✅ Research Report Ready")
            st.markdown(st.session_state.research_report)
            
            st.download_button(
                "📥 Download Report",
                data=st.session_state.research_report,
                file_name=f"research_{st.session_state.research_topic.replace(' ', '_')[:20]}.md",
                mime="text/markdown"
            )

def render_library_page(selected_model, ctx_size):
    """Render the Personal Knowledge Library page."""
    st.subheader("📚 Personal Knowledge Library")
    st.markdown("Upload documents, ask questions across your library, and get learning recommendations.")
    
    # Initialize library components in session state
    if "library_doc_store" not in st.session_state:
        st.session_state.library_doc_store = DocumentStore()
    if "library_vector_store" not in st.session_state:
        st.session_state.library_vector_store = VectorStore()
    if "library_pdf_processor" not in st.session_state:
        st.session_state.library_pdf_processor = PDFProcessor()
    if "library_rag_engine" not in st.session_state:
        st.session_state.library_rag_engine = RAGEngine(
            document_store=st.session_state.library_doc_store,
            vector_store=st.session_state.library_vector_store
        )
    if "library_chat_history" not in st.session_state:
        st.session_state.library_chat_history = []
    
    doc_store = st.session_state.library_doc_store
    vector_store = st.session_state.library_vector_store
    pdf_processor = st.session_state.library_pdf_processor
    rag_engine = st.session_state.library_rag_engine
    
    # Set summarizer for RAG engine
    if selected_model:
        rag_engine.set_summarizer(OllamaSummarizer(model=selected_model, num_ctx=ctx_size))
    
    # Layout: Two columns
    col_manage, col_qa = st.columns([1, 2])
    
    with col_manage:
        st.markdown("### 📁 Document Manager")
        
        # Upload Section
        with st.expander("📤 Upload Documents", expanded=True):
            uploaded_files = st.file_uploader(
                "Upload PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="library_uploader"
            )
            
            if uploaded_files:
                if st.button("📥 Add to Library", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"Processing: {uploaded_file.name}...")
                        
                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name
                        
                        try:
                            # Add to document store
                            doc_meta = doc_store.add_document(
                                tmp_path,
                                title=uploaded_file.name.replace(".pdf", "").replace("_", " ")
                            )
                            
                            # Process PDF
                            status_text.text(f"Extracting text: {uploaded_file.name}...")
                            result = pdf_processor.process_pdf(doc_meta["file_path"])
                            
                            if result.get("success"):
                                # Update metadata
                                doc_store.update_document(doc_meta["doc_id"], {
                                    "chapters": result.get("chapters", []),
                                    "chunk_count": result.get("chunk_count", 0)
                                })
                                
                                # Index chunks with document metadata
                                status_text.text(f"Indexing: {uploaded_file.name}...")
                                index_result = vector_store.index_document(
                                    doc_meta["doc_id"],
                                    result.get("chunks", []),
                                    doc_metadata=doc_meta
                                )
                                
                                if index_result.get("success"):
                                    doc_store.update_document(doc_meta["doc_id"], {"indexed": True})
                            
                        except Exception as e:
                            st.error(f"Error processing {uploaded_file.name}: {e}")
                        
                        finally:
                            # Cleanup temp file
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
                        
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    status_text.text("✅ All files processed!")
                    st.rerun()
        
        # Import Folder Section
        with st.expander("📂 Import from Folder (Google Drive)", expanded=False):
            st.caption("Import all PDFs from a folder (e.g., your Google Drive Books folder)")
            
            folder_path = st.text_input(
                "Folder Path",
                placeholder="G:\\My Drive\\Books or C:\\Users\\You\\Google Drive\\Books",
                key="library_folder_path"
            )
            
            if folder_path:
                from pathlib import Path
                import concurrent.futures
                from library.pdf_processor import process_pdf_worker
                
                # Clean the path
                folder_path = folder_path.strip().strip('"').strip("'")
                folder = Path(folder_path)
                
                # Debug info
                st.caption(f"📍 Checking: `{folder_path}`")
                
                if folder.exists() and folder.is_dir():
                    # Option to include subfolders
                    include_subfolders = st.checkbox("Include subfolders", value=True)
                    
                    # Count PDFs (only count once!)
                    if include_subfolders:
                        pdf_files = list(folder.glob("**/*.pdf"))
                    else:
                        pdf_files = list(folder.glob("*.pdf"))
                    
                    st.success(f"✅ Found {len(pdf_files)} PDF files")
                    
                    if pdf_files and st.button("📥 Import All PDFs (Parallel)", type="primary", key="import_folder_btn"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Stats
                        total_files = len(pdf_files)
                        completed_count = 0
                        skipped_count = 0
                        error_count = 0
                        
                        # Get list of already imported filenames for deduplication
                        existing_docs = doc_store.list_documents()
                        existing_file_map = {doc["filename"]: doc for doc in existing_docs}
                        
                        # Prepare files for processing
                        files_to_process = []
                        
                        # Pre-scan for existing files
                        for pdf_path in pdf_files:
                            if pdf_path.name in existing_file_map:
                                doc = existing_file_map[pdf_path.name]
                                if doc.get("indexed", False):
                                    skipped_count += 1
                                    continue
                                else:
                                    # Resume / Re-process
                                    doc_store.delete_document(doc["doc_id"], delete_file=False)
                            
                            files_to_process.append(str(pdf_path))
                        
                        # Update progress for skipped
                        if skipped_count > 0:
                            st.info(f"⏭️ Skipped {skipped_count} already indexed files.")
                            completed_count = skipped_count
                            progress_bar.progress(completed_count / total_files)
                        
                        if not files_to_process:
                            st.success("✅ All files are already up to date!")
                        else:
                            st.markdown("### 🚀 Starting Parallel Import Pipeline")
                            st.caption(f"Queue: {len(files_to_process)} documents")
                            
                            # Parallel Execution
                            # Safe number of workers:
                            # Use 2 workers by default for laptops to prevent 100% CPU lockup
                            # This leaves room for the OS, Streamlit, and the GPU driver
                            max_workers = 2
                            
                            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                                # Submit all tasks
                                future_to_file = {
                                    executor.submit(process_pdf_worker, f): f 
                                    for f in files_to_process
                                }
                                
                                status_text.markdown(f"**🔥 Workers Active**: {max_workers} processes extracting text...")
                                
                                # Process as they complete
                                for future in concurrent.futures.as_completed(future_to_file):
                                    original_file = future_to_file[future]
                                    filename = Path(original_file).name
                                    
                                    try:
                                        # 1. Get CPU Result (Text Extraction)
                                        result = future.result()
                                        
                                        if result.get("success"):
                                            # Create detailed log message
                                            page_count = result.get("page_count", 0)
                                            char_count = result.get("char_count", 0)
                                            chapter_count = len(result.get("chapters", []))
                                            chunk_count = result.get("chunk_count", 0)
                                            
                                            log_msg = f"""**📄 Processing**: `{filename}`
- ✅ Extracted {page_count} pages ({char_count:,} chars)
- 📑 Detected {chapter_count} chapters
- 🧩 Created {chunk_count} chunks
- 🧠 Generating embeddings (Model: bge-m3)..."""
                                            status_text.markdown(log_msg)
                                            
                                            # 2. Sequential/Main Thread Work (Metadata + GPU Embedding)
                                            # Add to document store
                                            doc_meta = doc_store.add_document(
                                                original_file,
                                                title=Path(original_file).stem.replace("_", " ").replace("-", " "),
                                                copy_file=False
                                            )
                                            
                                            # Update metadata
                                            doc_store.update_document(doc_meta["doc_id"], {
                                                "chapters": result.get("chapters", []),
                                                "chunk_count": result.get("chunk_count", 0)
                                            })
                                            
                                            # GPU WORK HERE - Main thread is blocked, but background workers continue parsing!
                                            index_result = vector_store.index_document(
                                                doc_meta["doc_id"],
                                                result.get("chunks", []),
                                                doc_metadata=doc_meta
                                            )
                                            
                                            if index_result.get("success"):
                                                doc_store.update_document(doc_meta["doc_id"], {"indexed": True})
                                            else:
                                                st.error(f"❌ Indexing failed for {filename}: {index_result.get('error')}")
                                                error_count += 1
                                                
                                        else:
                                            st.error(f"❌ Extraction failed for {filename}: {result.get('error')}")
                                            error_count += 1
                                            
                                    except Exception as exc:
                                        st.error(f"❌ Worker error for {filename}: {exc}")
                                        error_count += 1
                                    
                                    # Update Progress
                                    completed_count += 1
                                    progress_bar.progress(completed_count / total_files)
                        
                        st.success(f"✅ Import Complete! Processed: {len(files_to_process)} | Errors: {error_count}")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Folder not found. Please check the path.")
        
        # Library Stats
        stats = doc_store.get_stats()
        vector_stats = vector_store.get_stats()
        
        st.markdown("### 📊 Library Stats")
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Documents", stats.get("total_documents", 0))
        col_s2.metric("Indexed", stats.get("indexed_documents", 0))
        col_s3.metric("Chunks", vector_stats.get("total_chunks", 0))
        
        st.caption(f"Total size: {stats.get('total_size_mb', 0)} MB | Embedding: {vector_stats.get('embedding_model', 'N/A')}")
        
        # Reset Library button
        if stats.get("total_documents", 0) > 0:
            with st.expander("⚙️ Library Settings", expanded=False):
                st.warning("⚠️ This will delete all documents and vectors!")
                if st.button("🗑️ Reset Entire Library", type="secondary"):
                    vector_store.clear_all()
                    # Clear document store
                    for doc in doc_store.list_documents():
                        doc_store.delete_document(doc["doc_id"])
                    st.success("Library cleared! Refresh to start fresh.")
                    st.rerun()
        
        # Learning Path Generator
        with st.expander("🎯 Learning Path Generator", expanded=False):
            st.markdown("Get a suggested reading order for a topic based on your books.")
            
            learning_topic = st.text_input("Topic to learn", placeholder="e.g., Machine Learning fundamentals")
            
            if learning_topic and st.button("🎓 Generate Learning Path", type="primary"):
                if stats.get("indexed_documents", 0) == 0:
                    st.warning("⚠️ Please index some documents first!")
                else:
                    with st.spinner("Analyzing your library..."):
                        # Get all book titles
                        all_docs = doc_store.list_documents()
                        book_list = "\n".join([f"- {doc['title']}" for doc in all_docs[:50]])
                        
                        # Use LLM to create learning path
                        summarizer = OllamaSummarizer(model=selected_model, num_ctx=ctx_size)
                        
                        prompt = f"""You are a learning advisor. Given this topic and book list, create a learning path.

Topic to learn: {learning_topic}

Available books in library:
{book_list}

Create a numbered learning path that:
1. Starts with foundational books
2. Progresses to intermediate concepts
3. Ends with advanced material
4. Only include books from the list that are relevant

Format:
## 🎯 Learning Path: [Topic]

### Phase 1: Foundations
1. **[Book Title]** - [Why read this first]

### Phase 2: Core Concepts
2. **[Book Title]** - [What you'll learn]

### Phase 3: Advanced Topics
3. **[Book Title]** - [How this builds on previous]

If no relevant books exist, suggest what types of books to add."""

                        result = summarizer._generate_response(prompt)
                        
                        if result.get("success"):
                            st.markdown(result.get("summary", ""))
                        else:
                            st.error(f"Failed to generate learning path: {result.get('error')}")
        
        # Document List
        st.markdown("### 📖 Your Documents")
        documents = doc_store.list_documents()
        
        if not documents:
            st.info("No documents yet. Upload some PDFs to get started!")
        else:
            for doc in documents:
                with st.expander(f"📄 {doc['title']}", expanded=False):
                    st.caption(f"File: {doc['filename']}")
                    st.caption(f"Added: {doc['added_date'][:10]}")
                    st.caption(f"Indexed: {'✅' if doc.get('indexed') else '❌'}")
                    
                    if doc.get("chapters"):
                        st.markdown("**Chapters:**")
                        for ch in doc["chapters"][:5]:
                            st.caption(f"  • {ch.get('title', 'Untitled')}")
                    
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        if st.button("🔗 Open", key=f"open_{doc['doc_id']}"):
                            st.markdown(f"[Open File](file:///{doc['file_path']})")
                    with col_d2:
                        if st.button("🗑️ Delete", key=f"del_{doc['doc_id']}"):
                            vector_store.delete_document_chunks(doc["doc_id"])
                            doc_store.delete_document(doc["doc_id"])
                            st.rerun()
    
    with col_qa:
        st.markdown("### 💬 Ask Your Library")
        
        # Mode Selection
        mode = st.radio(
            "Mode:",
            ["🔍 Q&A", "📚 Learning Recommendations"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if mode == "🔍 Q&A":
            st.caption("Ask any question - I'll search your documents and provide answers with citations.")
            
            # Display chat history
            for msg in st.session_state.library_chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Input
            if prompt := st.chat_input("Ask a question about your documents..."):
                st.session_state.library_chat_history.append({"role": "user", "content": prompt})
                
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    try:
                        # Stream RAG response
                        stream_gen = rag_engine.query(prompt, top_k=5, stream=True)
                        
                        for chunk in stream_gen:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                        
                        message_placeholder.markdown(full_response)
                        st.session_state.library_chat_history.append({"role": "assistant", "content": full_response})
                        
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        message_placeholder.markdown(error_msg)
            
            # Clear history button
            if st.session_state.library_chat_history:
                if st.button("🗑️ Clear Chat"):
                    st.session_state.library_chat_history = []
                    st.rerun()
        
        else:  # Learning Recommendations
            st.caption("Tell me what you want to learn - I'll recommend relevant books and chapters from your library.")
            
            topic_input = st.text_input(
                "What do you want to learn?",
                placeholder="e.g., LangChain, prompt engineering, RAG systems..."
            )
            
            if st.button("🎯 Get Recommendations", type="primary", disabled=not topic_input):
                with st.spinner("Analyzing your library..."):
                    result = rag_engine.recommend_learning(topic_input, top_k=10)
                    
                    if result.get("success"):
                        st.markdown("### 📚 Learning Recommendations")
                        st.markdown(result.get("recommendations_text", "No recommendations found."))
                        
                        st.divider()
                        st.caption(f"Analyzed {result.get('chunks_analyzed', 0)} sections from {len(result.get('source_documents', []))} documents")
                    else:
                        st.warning(result.get("error", "Could not generate recommendations."))

