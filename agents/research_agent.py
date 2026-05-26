"""
Deep Research Agent
Searches the web and synthesizes multiple sources into a comprehensive report.
"""
from ddgs import DDGS
from extractors import WebPageExtractor
from summarizer import OllamaSummarizer
from evals.queue import LLMQueue, get_shared_llm_queue
import concurrent.futures

class ResearchAgent:
    def __init__(self, summarizer: OllamaSummarizer = None, llm_queue: LLMQueue = None):
        self.summarizer = summarizer or OllamaSummarizer()
        self.llm_queue = llm_queue or get_shared_llm_queue("ollama", max_concurrency=1)
        self.extractor = WebPageExtractor()

    def search_web(self, topic: str, max_results: int = 5) -> list[dict]:
        """Search DuckDuckGo for topic"""
        results = []
        
        try:
            # Use simple API call (v8+ compatible)
            with DDGS() as ddgs:
                search_results = ddgs.text(topic, max_results=max_results)
                for r in search_results:
                    results.append(r)
                    
        except Exception as e:
            print(f"DDG Search failed: {e}")
            # Return empty - will be handled by caller
                
        return results
    
    def _extract_single_source(self, res: dict) -> dict:
        """Extract content from a single source - helper for threading"""
        url = res.get('href')
        title = res.get('title')
        
        try:
            extraction = self.extractor.extract(url)
            if extraction['success']:
                return {
                    "title": title,
                    "url": url,
                    "text": extraction['text'][:10000]  # Limit per source
                }
        except Exception as e:
            print(f"Failed to extract {url}: {e}")
        return None

    def research_topic(self, topic: str, max_sources: int = 3, language: str = "th"):
        """
        Conduct deep research on a topic.
        Yields progress updates (str) or final result (dict).
        """
        yield f"🔎 Searching for '{topic}'..."
        
        # 1. Search
        search_results = self.search_web(topic, max_results=max_sources)
        if not search_results:
            yield "❌ No results found."
            return

        yield f"📚 Found {len(search_results)} sources. Reading content..."
        
        # 2. Extract Content (Parallel with thread pool)
        contents = []
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_res = {
                executor.submit(self._extract_single_source, res): res 
                for res in search_results
            }
            
            for i, future in enumerate(as_completed(future_to_res)):
                res = future_to_res[future]
                title = res.get('title', 'Unknown')
                yield f"📖 Reading ({i+1}/{len(search_results)}): {title}..."
                
                try:
                    result = future.result(timeout=15)
                    if result:
                        contents.append(result)
                except Exception as e:
                    print(f"Failed to extract {res.get('href')}: {e}")
        
        if not contents:
            yield "❌ Failed to extract content from any source."
            return



        # 3. Synthesize
        yield "🧠 Synthesizing report (Direct)..."
        
        combined_text = ""
        # Aggressive truncation to fit in context (4000 chars per source ~ 1000 tokens)
        MAX_CHARS_PER_SOURCE = 4000 
        
        for c in contents:
            snippet = c['text'][:MAX_CHARS_PER_SOURCE]
            combined_text += f"\n\n--- Source: {c['title']} ({c['url']}) ---\n{snippet}\n"

        prompt = self._get_research_prompt(topic, combined_text, language)
        
        # Stream the synthesis
        full_report = ""
        with self.llm_queue.slot():
            response_gen = self.summarizer._stream_response(prompt)
            for chunk in response_gen:
                full_report += chunk
                yield {"type": "chunk", "content": chunk}
            
        yield {"type": "complete", "report": full_report, "sources": search_results}

    def _get_research_prompt(self, topic: str, content: str, language: str) -> str:
        if language == "th":
            return f"""[IMPORTANT: ตอบเป็นภาษาไทยเท่านั้น และต้องละเอียดมากๆ]
คุณเป็นนักวิจัยระดับโลก หน้าที่ของคุณคือเขียน "รายงานการวิจัยเชิงลึก" (Deep Research Report) เกี่ยวกับหัวข้อ: "{topic}"

ข้อมูลดิบจากหลายแหล่ง:
{content}

คำสั่ง:
1. เขียนรายงานสรุปข้อมูลจากแหล่งต่างๆ เข้าด้วยกันอย่าง **ละเอียดที่สุดเท่าที่จะทำได้**
2. **ห้ามย่อความ**: เป้าหมายคือความสมบูรณ์ของเนื้อหา ไม่ใช่การสรุปสั้นๆ
3. วิเคราะห์เชิงลึก (Synthesize) เปรียบเทียบข้อมูลจากแหล่งต่างๆ หาความเชื่อมโยง
4. **ใช้ภาษาเชิงวิชาการ (Academic Tone)**: เน้นความน่าเชื่อถือ ไม่ใช้ Emoji หรือการตกแต่งที่ไม่จำเป็น
5. จัดรูปแบบให้อ่านง่ายด้วยหัวข้อและย่อหน้า

โครงสร้างรายงาน (ต้องครบถ้วน):
## บทนำ (Introduction)
[สรุปภาพรวมทั้งหมดโดยให้เนื้อหาครอบคลุมและสามรถอ่านได้เข้าใจตามวัตถุประสงค์ของทนำ]

## การวิเคราะห์เจาะลึก (Deep Dive Analysis)
[ส่วนนี้ต้องยาวที่สุด แยกเป็นหัวข้อย่อยตามประเด็นต่างๆ อธิบายละเอียด ลงลึก]
- ประเด็นที่ 1: ...
- ประเด็นที่ 2: ...

## ข้อมูลเชิงสถิติและข้อเท็จจริงหลัก (Key Facts & Stats)
- [ระบุตัวเลข สถิติ หรือข้อมูลสำคัญเป็นข้อๆ]


## บทสรุปและข้อเสนอแนะ (Conclusion & Insights)
[วิเคราะห์สรุปความเห็นของผู้เชี่ยวชาญ และแนวโน้มในอนาคต]

## แหล่งข้อมูลแนะนำสำหรับการศึกษาต่อ (Curated Further Study)
- **[ชื่อแหล่งข้อมูล](URL)**: [เหตุผลที่ควรอ่านต่อ]
  (หมายเหตุ: ใส่ลิงค์ URL เฉพาะหัวข้อที่มีไม่ต้องบังคับว่าหัวข้อที่ให้จะต้องมีลิงค์เท่านั้นคำนึงถึงประสิทธิภาพในการให้ผู้ใช้ได้ศึกษาต่อมากที่สุด)

เริ่มเขียนรายงานฉบับสมบูรณ์ (ความยาวไม่ต่ำกว่า 1500 คำ):"""
        else:
             return f"""Task: Write a comprehensive Deep Research Report on: "{topic}"

Raw Data from multiple sources:
{content}

Instructions:
1. Synthesize information into a **highly detailed** report.
2. **DO NOT SUMMARIZE**: Retain as much detail as possible. Aim for comprehensive coverage.
3. Analyze connections between sources and identify key trends.
4. **Academic Tone**: Professional and clean. DO NOT use Emojis.
5. Structure clearly with headings.

Structure:
## Executive Summary
[Overview in 1 paragraph]

## Deep Dive Analysis
[Main section. Break down into detailed subsections. Be exhaustive.]

## Key Facts & Statistics
[List important numbers and facts]

## Conclusion & Strategic Insights
[Final analysis and future outlook]

## Curated Further Study
- **[Resource Name](URL)**: [Why this resource is recommended]
  (Note: Include clickable URLs from the sources above for the 2-3 most relevant resources. Don't force links on every item.)

Start writing (Target length: 1000+ words):"""
