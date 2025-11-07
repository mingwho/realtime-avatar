#!/usr/bin/env python3
"""
Transcribe videos using OpenAI's Whisper to generate phrases.json automatically.

This extracts audio from videos and uses Whisper to create timestamped transcripts,
which can then be used to populate phrases.json.
"""

import subprocess
import json
import os
from pathlib import Path
import tempfile

def extract_audio(video_path: str, output_audio: str):
    """Extract audio from video using ffmpeg"""
    cmd = [
        'ffmpeg',
        '-y',
        '-i', video_path,
        '-vn',  # No video
        '-acodec', 'pcm_s16le',  # WAV format
        '-ar', '16000',  # 16kHz (Whisper standard)
        '-ac', '1',  # Mono
        output_audio
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def transcribe_with_whisper(audio_path: str, language: str = None):
    """
    Transcribe audio using Whisper with word-level timestamps.
    
    Returns list of segments with start/end times and text.
    """
    try:
        import whisper
        
        print(f"Loading Whisper model...")
        model = whisper.load_model("base")  # base model is good balance of speed/accuracy
        
        print(f"Transcribing {audio_path}...")
        result = model.transcribe(
            audio_path,
            language=language,
            word_timestamps=True,
            verbose=True
        )
        
        return result
        
    except ImportError:
        print("❌ Whisper not installed. Installing...")
        subprocess.run(['pip', 'install', 'openai-whisper'], check=True)
        print("✅ Installed! Please run the script again.")
        return None

def create_phrases_from_transcript(transcript, video_name: str, language: str, max_phrases: int = 3):
    """
    Create phrase entries from transcript segments.
    
    Selects diverse phrases (beginning, middle, end) of varying lengths.
    """
    segments = transcript['segments']
    
    if not segments:
        return []
    
    phrases = []
    
    # Strategy: Pick phrases from different parts of the video
    # 1. Beginning (0-20%)
    # 2. Middle (40-60%)
    # 3. End (80-100%)
    
    total_duration = segments[-1]['end']
    
    positions = [
        ('beginning', 0.0, 0.2),
        ('middle', 0.4, 0.6),
        ('end', 0.8, 1.0)
    ]
    
    phrase_id = 1
    
    for pos_name, start_pct, end_pct in positions[:max_phrases]:
        start_time = total_duration * start_pct
        end_time = total_duration * end_pct
        
        # Find segments in this range
        matching_segments = [
            s for s in segments
            if start_time <= s['start'] <= end_time
        ]
        
        if not matching_segments:
            continue
        
        # Pick the first clear segment in this range
        # (could be made smarter - e.g., pick longest, clearest, etc.)
        segment = matching_segments[0]
        
        # Determine difficulty based on length
        text_len = len(segment['text'].split())
        if text_len <= 5:
            difficulty = 'easy'
        elif text_len <= 12:
            difficulty = 'medium'
        else:
            difficulty = 'hard'
        
        phrase = {
            'id': f"{language}_{phrase_id:03d}",
            'text': segment['text'].strip(),
            'language': language,
            'source_video': video_name,
            'start_time': round(segment['start'], 2),
            'end_time': round(segment['end'], 2),
            'duration': round(segment['end'] - segment['start'], 2),
            'difficulty': difficulty,
            'use_case': pos_name,
            'notes': f"Auto-generated from transcript ({pos_name} of video)",
            'clip_path': f"clips/{language}_{phrase_id:03d}.mp4"
        }
        
        phrases.append(phrase)
        phrase_id += 1
    
    return phrases

def main():
    """Main transcription workflow"""
    
    script_dir = Path(__file__).parent
    assets_dir = script_dir.parent.parent / 'assets' / 'videos'
    
    videos_to_transcribe = [
        ('bruce_english.mp4', 'en'),
        ('bruce_mandarin.mp4', 'zh'),
        ('bruce_spanish.mp4', 'es'),
    ]
    
    all_phrases = []
    
    print("=" * 70)
    print("Automatic Phrase Generation via Whisper Transcription")
    print("=" * 70)
    print()
    
    for video_file, lang_code in videos_to_transcribe:
        video_path = assets_dir / video_file
        
        if not video_path.exists():
            print(f"⚠️  Skipping {video_file}: not found")
            continue
        
        print(f"\n📹 Processing: {video_file} (language: {lang_code})")
        print("-" * 70)
        
        # Extract audio to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
            tmp_audio_path = tmp_audio.name
        
        try:
            print("  1. Extracting audio...")
            extract_audio(str(video_path), tmp_audio_path)
            print("     ✅ Audio extracted")
            
            print("  2. Transcribing with Whisper...")
            # Map language codes
            whisper_lang = {
                'en': 'english',
                'zh': 'chinese',
                'es': 'spanish'
            }.get(lang_code, None)
            
            transcript = transcribe_with_whisper(tmp_audio_path, whisper_lang)
            
            if transcript is None:
                continue
            
            print("     ✅ Transcription complete")
            
            print("  3. Extracting phrases...")
            phrases = create_phrases_from_transcript(
                transcript,
                video_file,
                lang_code,
                max_phrases=2  # 2 phrases per video for MVP
            )
            
            for phrase in phrases:
                print(f"     • {phrase['id']}: \"{phrase['text'][:60]}...\" "
                      f"({phrase['start_time']}s - {phrase['end_time']}s)")
            
            all_phrases.extend(phrases)
            print(f"     ✅ Found {len(phrases)} phrases")
            
        finally:
            # Clean up temp audio
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)
    
    # Create phrases.json
    if all_phrases:
        output_config = {
            'version': '1.0',
            'description': 'Gold standard phrases auto-generated from Whisper transcription',
            'source_videos': {
                'english': '../assets/videos/bruce_english.mp4',
                'mandarin': '../assets/videos/bruce_mandarin.mp4',
                'spanish': '../assets/videos/bruce_spanish.mp4',
            },
            'phrases': all_phrases
        }
        
        output_file = script_dir / 'phrases.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_config, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print(f"✅ SUCCESS! Created phrases.json with {len(all_phrases)} phrases")
        print(f"📁 Location: {output_file}")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Review phrases.json to verify accuracy")
        print("  2. Run: python extract_clips.py")
        print("  3. Verify clips are correct")
        print("  4. Run gold set tests in evaluator")
        print()
    else:
        print("\n❌ No phrases generated. Check errors above.")

if __name__ == '__main__':
    main()
