import streamlit as st
from summarizer import OllamaSummarizer
from pages_ui import detect_content_type, extract_content


def render_batch_summary_page(selected_model, language, ctx_size):
    """Render the Batch URL Summarization page."""
    st.subheader("📋 Batch URL Summarization")
    
    # Check if we have URLs to process
    batch_urls = st.session_state.get("batch_urls", [])
    batch_results = st.session_state.get("batch_results", [])
    
    if not batch_urls and not batch_results:
        st.info("No URLs to process. Go to Home → Batch URLs to add URLs.")
        return
    
    st.markdown(f"**{len(batch_urls)} URLs** to process")
    
    # Process button
    if batch_urls and not batch_results:
        if st.button("🚀 Start Batch Processing", type="primary"):
            with st.spinner("Processing URLs..."):
                results = []
                progress = st.progress(0)
                status = st.empty()
                
                for i, url in enumerate(batch_urls):
                    status.markdown(f"Processing {i+1}/{len(batch_urls)}: `{url[:50]}...`")
                    
                    try:
                        # Extract content
                        ctype = detect_content_type(url)
                        extract_result = extract_content(ctype, url)
                        
                        if extract_result.get("success"):
                            content = extract_result.get("text", "")[:8000]  # Limit length
                            
                            # Summarize
                            summarizer = OllamaSummarizer(
                                model=selected_model,
                                timeout=300,
                                num_ctx=ctx_size
                            )
                            
                            # Non-streaming for batch
                            summary_result = summarizer.summarize(
                                content,
                                language=language,
                                content_type=ctype,
                                stream=False,
                            )
                            
                            if summary_result.get("success"):
                                results.append({
                                    "url": url,
                                    "title": extract_result.get("title", url[:30]),
                                    "summary": summary_result.get("summary", ""),
                                    "success": True
                                })
                            else:
                                results.append({
                                    "url": url,
                                    "error": summary_result.get("error", "Summary failed"),
                                    "success": False
                                })
                        else:
                            results.append({
                                "url": url,
                                "error": extract_result.get("error", "Extraction failed"),
                                "success": False
                            })
                            
                    except Exception as e:
                        results.append({
                            "url": url,
                            "error": str(e),
                            "success": False
                        })
                    
                    progress.progress((i + 1) / len(batch_urls))
                
                # Save results
                st.session_state.batch_results = results
                st.session_state.batch_urls = []  # Clear URLs after processing
                st.rerun()
    
    # Display results
    if batch_results:
        st.success(f"✅ Processed {len(batch_results)} URLs")
        
        # Stats
        success_count = sum(1 for r in batch_results if r.get("success"))
        st.markdown(f"**Success**: {success_count} | **Failed**: {len(batch_results) - success_count}")
        
        # Export all
        all_summaries = "\n\n---\n\n".join([
            f"## {r.get('title', r.get('url'))}\n\n{r.get('summary', r.get('error', 'Error'))}"
            for r in batch_results
        ])
        
        st.download_button(
            "📥 Download All Summaries",
            data=all_summaries,
            file_name="batch_summaries.md",
            mime="text/markdown"
        )
        
        st.divider()
        
        # Individual results
        for i, result in enumerate(batch_results):
            with st.expander(f"{'✅' if result.get('success') else '❌'} {result.get('title', result.get('url', f'Item {i+1}'))[:50]}", expanded=i==0):
                if result.get("success"):
                    st.markdown(result.get("summary", ""))
                else:
                    st.error(result.get("error", "Error"))
                st.caption(f"Source: {result.get('url', 'Unknown')}")
        
        # Clear button
        if st.button("🗑️ Clear Results"):
            st.session_state.batch_results = []
            st.session_state.batch_urls = []
            st.rerun()
