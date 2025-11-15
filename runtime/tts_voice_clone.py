#!/usr/bin/env python3
"""
Standalone TTS voice cloning script using XTTS-v2.
Runs in isolation to avoid NumPy conflicts with Ditto.
"""
import os
import sys
import torch
import torchaudio
import time
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

def synthesize_speech(text, speaker_wav, output_path, language="en"):
    """
    Synthesize speech using XTTS-v2 voice cloning.
    
    Args:
        text: Text to synthesize
        speaker_wav: Path to reference voice audio
        output_path: Path to save output audio
        language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi)
    """
    print(f"Loading XTTS-v2 model...")
    start_time = time.time()
    
    # Load model
    config = XttsConfig()
    config.load_json("/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/config.json")
    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config,
        checkpoint_dir="/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/",
        eval=True,
        use_deepspeed=False
    )
    
    # Move to GPU
    if torch.cuda.is_available():
        model.cuda()
        print("Using GPU for TTS")
    else:
        print("Using CPU for TTS")
    
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f}s")
    
    # Compute speaker latents from reference audio
    print(f"Computing speaker latents from: {speaker_wav}")
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=[speaker_wav]
    )
    
    # Synthesize
    print(f"Synthesizing: {text[:50]}...")
    synth_start = time.time()
    
    out = model.inference(
        text,
        language,
        gpt_cond_latent,
        speaker_embedding,
        temperature=0.7,  # Lower = more stable, higher = more expressive
        length_penalty=1.0,
        repetition_penalty=2.0,
        top_k=50,
        top_p=0.85,
    )
    
    synth_time = time.time() - synth_start
    
    # Save output
    audio_tensor = torch.tensor(out["wav"]).unsqueeze(0)
    torchaudio.save(output_path, audio_tensor, 24000)
    
    audio_duration = len(out["wav"]) / 24000
    rtf = synth_time / audio_duration
    
    print(f"\nSynthesis complete:")
    print(f"  Audio duration: {audio_duration:.2f}s")
    print(f"  Synthesis time: {synth_time:.2f}s")
    print(f"  RTF: {rtf:.2f}x")
    print(f"  Output: {output_path}")
    
    return output_path, audio_duration

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python tts_voice_clone.py <text> <speaker_wav> <output_wav> [language]")
        print("Example: python tts_voice_clone.py 'Hello world' /root/bruce_voice_sample.wav /root/output.wav en")
        sys.exit(1)
    
    text = sys.argv[1]
    speaker_wav = sys.argv[2]
    output_path = sys.argv[3]
    language = sys.argv[4] if len(sys.argv) > 4 else "en"
    
    if not os.path.exists(speaker_wav):
        print(f"Error: Speaker audio not found: {speaker_wav}")
        sys.exit(1)
    
    synthesize_speech(text, speaker_wav, output_path, language)
