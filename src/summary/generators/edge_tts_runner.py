import sys
import json
import os
import asyncio
import edge_tts

async def generate_segment(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

async def process_tts(script_path, output_dir):
    """
    Batch process TTS script using Edge TTS.
    """
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading script JSON: {e}")
        sys.exit(1)
        
    script_items = data.get("script", [])
    
    # Define voices
    # Host A = Female = Premwadee
    # Host B = Male = Niwat
    VOICE_FEMALE = "th-TH-PremwadeeNeural"
    VOICE_MALE = "th-TH-NiwatNeural"
    
    # You can also pass voice_map in json to override
    voice_map = data.get("voice_map", {})
    
    success_count = 0
    tasks = []
    
    print(f"Starting Edge TTS Batch for {len(script_items)} segments...")
    
    for i, item in enumerate(script_items):
        text = item.get("text", "").strip()
        speaker = item.get("speaker", "A")
        
        if not text:
            continue
            
        out_path = os.path.join(output_dir, f"seg_{i:03d}.mp3")
        
        # Determine voice
        voice = VOICE_FEMALE
        if speaker == "B":
            voice = VOICE_MALE
            
        # Override from map if present
        if speaker in voice_map:
            voice = voice_map[speaker]
            
        # Create Task
        print(f"[{i+1}] Generating ({speaker}): {text[:30]}...")
        tasks.append(generate_segment(text, voice, out_path))
        success_count += 1
    
    # Run all async (or chunked if too many)
    # Edge TTS is online, so parallel requests might be rate limited? 
    # Let's do it sequentially to be safe or semi-parallel?
    # Edge TTS CLI does specific buffering. Let's try simple await in loop for stability first.
    
    for i, item in enumerate(script_items):
        text = item.get("text", "").strip()
        speaker = item.get("speaker", "A")
        if not text: continue
        
        out_path = os.path.join(output_dir, f"seg_{i:03d}.mp3")
        voice = VOICE_FEMALE
        if speaker == "B": voice = VOICE_MALE
        if speaker in voice_map: voice = voice_map[speaker]

        try:
            await generate_segment(text, voice, out_path)
        except Exception as e:
            print(f"Error segment {i}: {e}")

    print(f"Batch Processing Complete. {success_count} segments processed.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python edge_tts_runner.py <script_json> <output_dir>")
        sys.exit(1)
        
    script_json = sys.argv[1]
    out_dir = sys.argv[2]
    
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(process_tts(script_json, out_dir))
