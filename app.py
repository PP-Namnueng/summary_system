"""
Knowledge Summary System - Main Streamlit Application
สรุปความรู้จากหลายแหล่ง (YouTube, Web, PDF, Text) ด้วย AI
"""
import streamlit as st
from extractors import YouTubeExtractor, WebPageExtractor, PDFExtractor
from summarizer import OllamaSummarizer
from integrations import find_obsidian_vaults
from agents.observer import ObserverAgent # Autopilot
from agents.sentinel import SentinelAgent
import re
from pages_ui import (
    render_sentinel, 
    render_autopilot, 
    render_deep_research,
    render_library_page,
    render_summary_page,
    render_chat_page,
    render_podcast_page,
    render_home_page,
    extract_content,      # Imported
    detect_content_type   # Imported
)

# Page configuration
st.set_page_config(
    page_title="📚 Knowledge Summary System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS & Assets Injection - REMOVED




def initialize_session_state():
    """Initialize session state variables"""
    if "summary_result" not in st.session_state:
        st.session_state.summary_result = None
    if "extracted_content" not in st.session_state:
        st.session_state.extracted_content = None
    if "ollama_connected" not in st.session_state:
        st.session_state.ollama_connected = False
    if "source_url" not in st.session_state:
        st.session_state.source_url = None
    if "content_type" not in st.session_state:
        st.session_state.content_type = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "observer_agent" not in st.session_state:
        st.session_state.observer_agent = None
    
    # Navigation State
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "🏠 Home"
    
    # Redirect Flag
    if "redirect_to_summary" in st.session_state and st.session_state.redirect_to_summary:
        st.session_state.app_mode = "📝 Summary"
        st.session_state.redirect_to_summary = False # Reset flag

    if "sentinel_agent" not in st.session_state:
        st.session_state.sentinel_agent = SentinelAgent()

    # Busy State & Persistence
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "research_report" not in st.session_state:
        st.session_state.research_report = ""
    if "research_error" not in st.session_state:
        st.session_state.research_error = None


@st.cache_resource(ttl=60)
def get_ollama_client():
    """Get cached Ollama summarizer instance"""
    try:
        return OllamaSummarizer()
    except Exception:
        return None


@st.cache_data(ttl=30)
def check_ollama_connection():
    """Check if Ollama is running (cached for 30s)"""
    try:
        client = get_ollama_client()
        return client.check_connection() if client else False
    except Exception:
        return False


@st.cache_data(ttl=60)
def get_cached_models():
    """Get available models (cached for 60s)"""
    try:
        client = get_ollama_client()
        return client.get_available_models() if client else []
    except Exception:
        return []


@st.cache_data(ttl=300)
def get_cached_vaults():
    """Get Obsidian vaults (cached for 5 min)"""
    return find_obsidian_vaults()


def main():
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.header("🧭 Navigation")
        # Flattened Sidebar Menu linked to session_state
        app_mode = st.radio(
            "Go to:",
            [
                "🏠 Home",
                "🛡️ Sentinel",
                "👁️ Autopilot",
                "🕵️‍♂️ Deep Research",
                "📚 Library",
                "📝 Summary",
                "💬 Chat", 
                "🎧 Podcast"
            ],
            key="app_mode", # Links to st.session_state.app_mode
            label_visibility="collapsed",
            disabled=st.session_state.is_processing
        )
        st.divider()

        # --- INPUT SECTION (Only show if NOT Home) ---
        # Optional: Hide input on home to avoid redundancy, or keep for consistency.
        # User requested: "input box will then 'move' to the sidebar" implying it's not there initially or changes.
        # Let's hide it on Home to give "Landing Page" feel.
        
        if app_mode != "🏠 Home":
            with st.expander("📥 Content Input", expanded=(not st.session_state.extracted_content)):
                # Input type selection
                input_type = st.radio(
                    "Input Type",
                    options=["🔗 URL", "📄 PDF", "📝 Text"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if "URL" in input_type:
                    url_input = st.text_input(
                        "URL (YouTube/Web)",
                        placeholder="https://...",
                        key="sidebar_url_input"
                    )
                    
                    if st.button("📥 Extract", type="primary", use_container_width=True, key="sidebar_extract_btn"):
                        if url_input:
                            detected_type = detect_content_type(url_input)
                            with st.spinner("Extracting..."):
                                result = extract_content(detected_type, url_input)
                                if result.get("success"):
                                    st.session_state.extracted_content = result
                                    st.session_state.source_url = url_input
                                    st.session_state.content_type = detected_type
                                    st.success(f"✅ Ready ({len(result.get('text', ''))} chars)")
                                else:
                                    st.error(f"❌ {result.get('error')}")
                
                elif "PDF" in input_type:
                    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="sidebar_pdf_input")
                    if uploaded_file and st.button("📥 Extract PDF", type="primary", use_container_width=True, key="sidebar_pdf_btn"):
                         with st.spinner("Extracting PDF..."):
                            pdf_bytes = uploaded_file.read()
                            result = extract_content("pdf", pdf_bytes, uploaded_file.name)
                            if result.get("success"):
                                st.session_state.extracted_content = result
                                st.session_state.source_url = None
                                st.session_state.content_type = "pdf"
                                st.success(f"✅ Ready ({len(result.get('text', ''))} chars)")
                            else:
                                st.error(f"❌ {result.get('error')}")
                                
                else: # Text
                    text_input = st.text_area("Paste Text", height=150, key="sidebar_text_input")
                    if text_input and st.button("Use Text", type="primary", use_container_width=True, key="sidebar_text_btn"):
                        st.session_state.extracted_content = {"text": text_input, "success": True}
                        st.session_state.source_url = None
                        st.session_state.content_type = "text"
                        st.success("✅ Text Ready")

            # Preview Section
            if st.session_state.extracted_content and st.session_state.extracted_content.get("success"):
                with st.expander("📄 Content Preview", expanded=False):
                    preview_text = st.session_state.extracted_content.get("text", "")
                    if len(preview_text) > 500:
                        st.caption(f"Showing 500 of {len(preview_text)} chars")
                        st.code(preview_text[:500] + "...", language="text")
                    else:
                        st.code(preview_text, language="text")

            st.divider()
        
        st.header("⚙️ Settings")
        
        # Language selection
        language = st.selectbox(
            "🌐 Output Language",
            options=["th", "en"],
            format_func=lambda x: "🇹🇭 ภาษาไทย" if x == "th" else "🇬🇧 English",
            index=0,
        )
        
        # Theme Selector - REMOVED

        
        # Model selection
        st.subheader("🤖 AI Model")
        
        # Check Ollama connection
        ollama_status = check_ollama_connection()
        
        selected_model = None
        if ollama_status:
            available_models = get_cached_models()
            if available_models:
                selected_model = st.selectbox(
                    "Select Model",
                    options=available_models,
                    index=0,
                )
            else:
                st.warning("No models found")
        else:
            st.error("❌ Ollama Offline")
        
        # Context Window
        ctx_size = st.slider(
            "Context (Tokens)",
            min_value=2048,
            max_value=262144, # 256k
            value=8192,
            step=1024,
            help="Increase for long videos/PDFs. Qwen-2.5-7b-instruct-1M supports up to 1M."
        )
        
        st.divider()
        
        # Obsidian Integration
        st.subheader("📝 Obsidian")
        
        # Try to find vaults (cached)
        detected_vaults = get_cached_vaults()
        
        obsidian_enabled = st.toggle("Enable", value=False)
        
        vault_path = None
        summary_folder = "Summaries"
        auto_save = False

        if obsidian_enabled:
            if detected_vaults:
                vault_path = st.selectbox(
                    "Select Vault",
                    options=detected_vaults + ["Custom..."],
                )
                if vault_path == "Custom...":
                    vault_path = st.text_input("Path", placeholder="C:/...")
            else:
                vault_path = st.text_input("Vault Path", placeholder="C:/...")
            
            summary_folder = st.text_input("Folder", value="Summaries")
            auto_save = st.checkbox("Auto-save", value=True)
            
        st.divider()
        st.caption(f"Sentinel: {'Active' if 'sentinel_agent' in st.session_state else 'Inactive'}")

    # --- MAIN CONTENT DISPATCHER ---
    
    if app_mode == "🏠 Home":
        render_home_page()
    
    elif app_mode == "🛡️ Sentinel":
        render_sentinel(st.session_state.sentinel_agent, selected_model)
        
    elif app_mode == "👁️ Autopilot":
        # Check init
        if st.session_state.observer_agent is None:
             st.session_state.observer_agent = ObserverAgent(model_name=selected_model or "llama3.1")
        render_autopilot(st.session_state.observer_agent, selected_model)
    
    elif app_mode == "🕵️‍♂️ Deep Research":
        render_deep_research(selected_model, language, ctx_size)

    elif app_mode == "📚 Library":
        render_library_page(selected_model, ctx_size)

    elif app_mode == "📝 Summary":
        render_summary_page(selected_model, language, ctx_size, obsidian_enabled, vault_path, summary_folder, auto_save)
    
    elif app_mode == "💬 Chat":
        render_chat_page(selected_model, ctx_size)
    
    elif app_mode == "🎧 Podcast":
        render_podcast_page(selected_model, ctx_size)
    
    elif app_mode == "📋 Batch Summary":
        from batch_summary import render_batch_summary_page
        render_batch_summary_page(selected_model, language, ctx_size)

    # Footer
    st.divider()
    st.caption("Powered by Local LLMs (Ollama)")

if __name__ == "__main__":
    main()
