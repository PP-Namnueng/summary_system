import sys
import json
import os
import time
import torch

# Monkeypatch torch.load to fix "WeightsUnpickler error" on newer torch versions
# which default weights_only=True, breaking older TTS models.
_original_load = torch.load
def safe_load(*args, **kwargs):
    # Only available in newer torch, but safe to pass if kwargs accepts it?
    # No, older torch doesn't have weights_only arg.
    # We should catch TypeError or check version?
    # Or just try to set it if safe.
    # But usually this error comes from newer torch where it IS available.
    if 'weights_only' not in kwargs:
        try:
            return _original_load(*args, **kwargs, weights_only=False)
        except TypeError:
            # Fallback for older torch that doesn't support weights_only
            return _original_load(*args, **kwargs)
    return _original_load(*args, **kwargs)

torch.load = safe_load

def process_tts(script_path, output_dir, model_name="tts_models/multilingual/multi-dataset/xtts_v2"):
    """
    Batch process TTS script using Coqui TTS.
    """
    try:
        from TTS.api import TTS
    except ImportError:
        print("Error: TTS not installed in this environment.")
        sys.exit(1)

    print(f"Loading TTS Model: {model_name}")
    start_load = time.time()
    
    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    try:
        tts = TTS(model_name).to(device)
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
        
    print(f"Model loaded in {time.time() - start_load:.2f}s")

    # Load Script
    with open(script_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    script_items = data.get("script", [])
    voice_map = data.get("voice_map", {})
    
    # Default voices if not provided in map (Fallback)
    # voices/female_ref.wav should be passed in voice_map if available
    
    success_count = 0
    
    for i, item in enumerate(script_items):
        text = item.get("text", "").strip()
        speaker = item.get("speaker", "A")
        
        if not text:
            continue
            
        # Determine output path
        out_path = os.path.join(output_dir, f"seg_{i:03d}.wav")
        
        # Get speaker ref file or speaker name
        # Prioritize cloning with speaker_wav if provided in voice_map
        speaker_wav = voice_map.get(speaker)
        
        # TTS Call
        print(f"[{i+1}/{len(script_items)}] Generating ({speaker})...")
        try:
            # Arguments for tts_to_file vary by model. XTTS uses speaker_wav usually.
            if speaker_wav and os.path.exists(speaker_wav):
                tts.tts_to_file(
                    text=text, 
                    file_path=out_path, 
                    speaker_wav=speaker_wav, 
                    language="th" # Hardcoded to Thai as per user context, or could be passed
                )
            else:
                # If no reference audio, fall back to predefined speakers if supported
                # XTTS v2 requires speaker_wav for cloning or speaker_idx for pre-baked?
                # XTTS usually needs a reference audio.
                # If we don't have one, we might fail or need a default one.
                print(f"Warning: No valid speaker_wav for {speaker}. Skipping?")
                # Create a silent file or error? 
                # Let's try to assume there is a default if specific map missing?
                # Actually, podcast_generator.py has REF_FEMALE/REF_MALE.
                # We expect them to be passed in voice_map.
                continue
                
            success_count += 1
            
        except Exception as e:
            # Avoid using emojis in print on Windows consoles with cp874/cp1252
            print(f"Error generating line {i}: {e}")
            
    print(f"Batch Processing Complete. {success_count}/{len(script_items)} segments generated.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tts_runner.py <script_json> <output_dir>")
        sys.exit(1)
        
    script_json = sys.argv[1]
    out_dir = sys.argv[2]
    
    process_tts(script_json, out_dir)
