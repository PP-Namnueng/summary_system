"""
Podcast Generator
Converts text summaries into audio podcasts using Edge TTS (via Python 3.11 env)
"""
import json
import re
import tempfile
import os
import subprocess
import shutil
from typing import List, Dict
from summary.summarizer import OllamaSummarizer
from pydub import AudioSegment

class PodcastGenerator:
    """Generate audio podcasts using Microsoft Edge TTS (via tts_env)"""
    
    # Path to Python 3.11 TTS environment
    TTS_PYTHON_EXE = os.path.join(os.getcwd(), "tts_env", "Scripts", "python.exe")
    # New Edge TTS Runner
    TTS_RUNNER = os.path.join(os.getcwd(), "generators", "edge_tts_runner.py")
    
    # Reference files are no longer used for cloning but kept for compatibility logic if needed
    REF_FEMALE = os.path.join(os.getcwd(), "voices", "female_ref.wav")
    REF_MALE = os.path.join(os.getcwd(), "voices", "male_ref.wav")
    
    def __init__(self, summarizer: OllamaSummarizer = None):
        self.summarizer = summarizer or OllamaSummarizer()
        
        # Ensure voices dir exists
        if not os.path.exists("voices"):
            os.makedirs("voices")

    def generate_script(self, summary: str, language: str = "th", style: str = "regular") -> tuple[List[Dict[str, str]], str]:
        """Generate Script using Ollama"""
        prompt = self._get_script_prompt(summary, language)
        response = self.summarizer._generate_response(prompt)
        
        if not response.get("success"):
            return [], response.get("error")
            
        return self._parse_script(response.get("summary", "")), None

    def generate_audio(self, script: List[Dict[str, str]], output_file: str, voice_a_path: str = None, voice_b_path: str = None) -> tuple[bool, str]:
        """
        Generate audio using EDGE TTS (Batch).
        Ignores custom voice paths in favor of high-quality Edge Voices (Premwadee/Niwat).
        """
        
        # Check if python env exists
        if not os.path.exists(self.TTS_PYTHON_EXE):
            return False, "TTS python env not found. Please install Python 3.11 and check tts_env."
            
        # Create a temporary directory for batch processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Prepare JSON Payload
            payload = {
                "script": script
            }
            
            script_json_path = os.path.join(temp_dir, "batch_script.json")
            with open(script_json_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                
            # 2. Call edge_tts_runner.py
            cmd = [
                self.TTS_PYTHON_EXE,
                self.TTS_RUNNER,
                script_json_path,
                temp_dir
            ]
            
            print(f"Launching Edge TTS... (Output: {temp_dir})")
            try:
                # Capture output for debugging
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode != 0:
                    print(f"Edge TTS Runner Failed:\n{result.stderr}")
                    return False, f"Edge TTS Runner Failed: {result.stderr}"
                else:
                    print(f"Edge TTS Runner Success:\n{result.stdout}")
                    
                # 3. Collect and Merge Segments
                # Edge TTS runner outputs .mp3 files
                files = sorted([f for f in os.listdir(temp_dir) if f.startswith("seg_") and f.endswith(".mp3")])
                
                if not files:
                    return False, "No audio segments generated."
                
                # Verify format from extension
                ext = "mp3"
                if output_file.lower().endswith(".wav"):
                   # If user requested WAV, we are stuck without FFMPEG to convert MP3->WAV
                   # But let's fallback to forcing MP3 since Edge TTS is native MP3
                   print("Warning: Edge TTS outputs MP3. Output will be MP3 despite .wav extension request if FFMPEG is missing.")
                   ext = "mp3"
                   if not output_file.lower().endswith(".mp3"):
                       output_file = os.path.splitext(output_file)[0] + ".mp3"

                print("Merging segments (Binary Concatenation)...")
                with open(output_file, 'wb') as outfile:
                    for fname in files:
                        fpath = os.path.join(temp_dir, fname)
                        with open(fpath, 'rb') as readfile:
                            shutil.copyfileobj(readfile, outfile)
                            
                return True, None
                
            except Exception as e:
                return False, str(e)

    def _parse_script(self, raw_text: str) -> List[Dict[str, str]]:
        """Parse LLM output into struct"""
        try:
            cleaned_text = raw_text.strip()
            if "```" in cleaned_text:
                pattern = r"```(?:json)?(.*?)```"
                match = re.search(pattern, cleaned_text, re.DOTALL)
                if match:
                    cleaned_text = match.group(1).strip()
            
            try:
                start = cleaned_text.find('[')
                end = cleaned_text.rfind(']')
                if start != -1 and end != -1:
                    json_candidate = cleaned_text[start:end+1]
                    return json.loads(json_candidate)
            except json.JSONDecodeError:
                pass
            
            script = []
            lines = raw_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue
                speaker_match = re.match(r"(?:\*\*|\[)?(?:Host\s+)?([AB]|[ABCD])(?:\*\*|\])?\s*[:\-\)]\s*(.*)", line, re.IGNORECASE)
                if speaker_match:
                    speaker_code = speaker_match.group(1).upper()
                    text = speaker_match.group(2).strip()
                    if "A" in speaker_code: speaker = "A"
                    elif "B" in speaker_code: speaker = "B"
                    else: speaker = "A"
                    if text:
                        script.append({"speaker": speaker, "text": text})
            return script
        except Exception:
            return []

    def _get_script_prompt(self, summary: str, language: str) -> str:
        return f"""Task: Convert summary to Podcast Script (Thai).
Role: Podcast Producer.
Hosts:
- Host A (Female): "Khun Prem" (Polite, friendly)
- Host B (Male): "Khun Niwat" (Expert, calm)
Format: JSON list [ {{"speaker": "A", "text": "..."}} ]
Summary: {summary}"""

    def _get_debate_prompt(self, summary: str, language: str) -> str:
        return f"""Task: Convert summary to DEBATE Script (Thai).
Role: Drama Producer.
Hosts:
- Host A (Female): "Khun Prem" (Believer)
- Host B (Male): "Khun Niwat" (Skeptic)
Format: JSON list [ {{"speaker": "A", "text": "..."}} ]
Summary: {summary}"""

    def _get_news_prompt(self, summary: str, language: str) -> str:
        return f"""Task: Convert summary to NEWS Script (Thai).
Role: News Director.
Hosts:
- Host A (Female): "Anchor Prem"
- Host B (Male): "Reporter Niwat"
Format: JSON list [ {{"speaker": "A", "text": "..."}} ]
Summary: {summary}"""

    def _get_story_prompt(self, summary: str, language: str) -> str:
        return f"""Task: Convert summary to STORYTELLER Script (Thai).
Role: Storyteller.
Hosts:
- Host A (Female): Narrator
- Host B (Male): Guide
Format: JSON list [ {{"speaker": "A", "text": "..."}} ]
Summary: {summary}"""

    def _get_interactive_prompt(self, history: List[Dict[str, str]], user_input: str, language: str) -> str:
        return f"""Task: Generate Host Response (Thai).
Listener said: "{user_input}"
Goal: Acknowledge and discuss briefly.
Format: JSON list [ {{"speaker": "A", "text": "..."}} ]"""

if __name__ == "__main__":
    gen = PodcastGenerator()
    script = gen.generate_script("ทดสอบ...", "th")
    print(script)
