#!/usr/bin/env python3
"""
Complete pipeline: Text → XTTS voice cloning → Ditto TensorRT lip sync
"""
import os
import sys
import time
import subprocess
import argparse

def run_tts(text, speaker_wav, output_audio, language="en"):
    """Run TTS voice cloning in separate process to avoid NumPy conflicts"""
    print(f"\n{'='*60}")
    print("STEP 1: Text-to-Speech with Voice Cloning")
    print(f"{'='*60}")
    
    cmd = [
        "python3", "/root/tts_voice_clone.py",
        text,
        speaker_wav,
        output_audio,
        language
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("TTS Error:", result.stderr)
        return None
    
    # Parse duration from output
    for line in result.stdout.split('\n'):
        if 'Audio duration:' in line:
            duration = float(line.split(':')[1].strip().replace('s', ''))
            return duration
    
    return None

def run_ditto_trt(image_path, audio_path, output_video):
    """Run Ditto TensorRT lip sync"""
    print(f"\n{'='*60}")
    print("STEP 2: Ditto TensorRT Lip Sync")
    print(f"{'='*60}")
    
    cmd = [
        "python3", "/app/runtime/benchmark_ditto_trt.py",
        "--source_path", image_path,
        "--audio_path", audio_path,
        "--output_path", output_video
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Ditto Error:", result.stderr)
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Complete voice cloning + lip sync pipeline")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--speaker", required=True, help="Path to speaker reference audio")
    parser.add_argument("--image", required=True, help="Path to face image")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--language", default="en", help="Language code (en, es, zh-cn, etc.)")
    parser.add_argument("--resolution", default="384x579", help="Output resolution")
    parser.add_argument("--steps", type=int, default=25, help="Diffusion steps")
    parser.add_argument("--audio-output", default="/tmp/tts_audio.wav", help="Temp audio file")
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("COMPLETE VOICE CLONING + LIP SYNC PIPELINE")
    print(f"{'='*60}")
    print(f"Text: {args.text[:100]}...")
    print(f"Speaker: {args.speaker}")
    print(f"Image: {args.image}")
    print(f"Output: {args.output}")
    print(f"Language: {args.language}")
    print(f"Resolution: {args.resolution}")
    print(f"Diffusion steps: {args.steps}")
    
    total_start = time.time()
    
    # Step 1: TTS
    audio_duration = run_tts(args.text, args.speaker, args.audio_output, args.language)
    if audio_duration is None:
        print("ERROR: TTS failed")
        return 1
    
    # Step 2: Ditto TRT
    success = run_ditto_trt(args.image, args.audio_output, args.output)
    if not success:
        print("ERROR: Ditto TRT failed")
        return 1
    
    total_time = time.time() - total_start
    total_rtf = total_time / audio_duration if audio_duration > 0 else 0
    
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Audio duration: {audio_duration:.2f}s")
    print(f"End-to-end RTF: {total_rtf:.2f}x")
    print(f"Output video: {args.output}")
    
    # Cleanup temp audio
    if os.path.exists(args.audio_output):
        os.remove(args.audio_output)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
