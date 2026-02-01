from gtts import gTTS
import os

def generate_gtts():
    text = "นี่คือการทดสอบเสียงภาษาไทยจาก Google TTS ครับ"
    print("Generating gTTS...")
    tts = gTTS(text, lang='th')
    tts.save("sample_gtts.mp3")
    print("Saved sample_gtts.mp3")

if __name__ == "__main__":
    generate_gtts()
