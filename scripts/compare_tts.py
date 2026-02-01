import asyncio
import os
import edge_tts

async def generate_samples():
    text = "นี่คือการทดสอบเสียงภาษาไทยครับ เรามารอดูกันว่าเสียงเป็นอย่างไรบ้าง"
    
    # 1. Edge TTS - Male (Niwat)
    print("Generating Edge TTS (Niwat)...")
    communicate = edge_tts.Communicate(text, "th-TH-NiwatNeural")
    await communicate.save("sample_edge_niwat.mp3")
    
    # 2. Edge TTS - Female (Premwadee)
    print("Generating Edge TTS (Premwadee)...")
    communicate = edge_tts.Communicate(text, "th-TH-PremwadeeNeural")
    await communicate.save("sample_edge_premwadee.mp3")
    
    print("Done! Files saved: sample_edge_niwat.mp3, sample_edge_premwadee.mp3")

if __name__ == "__main__":
    loop = asyncio.get_event_loop_policy().get_event_loop()
    loop.run_until_complete(generate_samples())
