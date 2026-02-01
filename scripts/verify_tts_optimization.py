import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators.podcast_generator import PodcastGenerator

def test_optimization():
    print("Initializing Generator...")
    gen = PodcastGenerator()
    
    # Check voices
    male_voice = os.path.join("voices", "male_ref.wav")
    if not os.path.exists(male_voice):
        print(f"Error: {male_voice} not found. Cannot test.")
        return

    # Use male voice for both to avoid missing file issues
    voice_a = male_voice
    voice_b = male_voice
    
    print(f"Testing with voice: {male_voice}")
    
    # Dummy Script
    script = [
        {"speaker": "A", "text": "This is a test of the optimized system."}, # English text might work if model is multilingual, but user used Thai. XTTS is multilingual.
        {"speaker": "B", "text": "It should be much faster now."}
    ]
    
    output_file = "test_output_opt.mp3"
    if os.path.exists(output_file):
        os.remove(output_file)
        
    print("Generating Audio...")
    # Generator handles extension logic, but we request mp3 explicitly to match expectations
    success, error = gen.generate_audio(script, output_file, voice_a_path=voice_a, voice_b_path=voice_b)
    
    if success:
        print(f"[SUCCESS] Audio saved to {output_file}")
        # Verify size
        size = os.path.getsize(output_file)
        print(f"File size: {size} bytes")
    else:
        print(f"[FAIL] Failed: {error}")

if __name__ == "__main__":
    test_optimization()
