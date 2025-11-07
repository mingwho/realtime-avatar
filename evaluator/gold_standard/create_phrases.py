#!/usr/bin/env python3
"""
Interactive helper to create gold standard phrases.json

This script helps you watch your videos and note down phrases with timestamps.
"""

import json
import subprocess
from pathlib import Path

def play_video_segment(video_path: str, start_time: float = 0):
    """Play video from a specific timestamp using ffplay"""
    cmd = [
        'ffplay',
        '-ss', str(start_time),
        '-autoexit',
        video_path
    ]
    subprocess.run(cmd)

def interactive_phrase_builder():
    """Interactively build phrases.json"""
    
    script_dir = Path(__file__).parent
    template_file = script_dir / 'phrases_template.json'
    output_file = script_dir / 'phrases.json'
    
    # Load template
    with open(template_file, 'r') as f:
        config = json.load(f)
    
    print("=" * 70)
    print("Gold Standard Phrase Builder")
    print("=" * 70)
    print("\nThis tool helps you create phrases.json by watching your videos")
    print("and noting specific phrases with timestamps.\n")
    
    print("Available source videos:")
    for key, path in config['source_videos'].items():
        print(f"  - {key}: {path}")
    
    print("\n" + "=" * 70)
    print("Current phrases in template:")
    print("=" * 70)
    
    for i, phrase in enumerate(config['phrases'], 1):
        print(f"\n{i}. Phrase ID: {phrase['id']}")
        print(f"   Language: {phrase['language']}")
        print(f"   Source: {phrase['source_video']}")
        print(f"   Time: {phrase['start_time']}s - {phrase['end_time']}s")
        print(f"   Text: {phrase['text']}")
        print(f"   Difficulty: {phrase['difficulty']}")
        print(f"   Use case: {phrase['use_case']}")
    
    print("\n" + "=" * 70)
    print("INSTRUCTIONS:")
    print("=" * 70)
    print("""
1. Watch your source videos (bruce_english.mp4, bruce_mandarin.mp4, etc.)
   
2. For each video, identify 2-3 clear phrases where you're speaking:
   - Note the exact text spoken
   - Note the start and end timestamps
   - Vary the length (short, medium, long)
   
3. Edit phrases_template.json directly:
   - Replace 'REPLACE_WITH_ACTUAL_TEXT' with actual spoken text
   - Update start_time and end_time to match your videos
   - Add more phrase objects as needed
   
4. Save as phrases.json

5. Run: python extract_clips.py
   This will create video clips from your timestamps

6. Verify the clips look correct

7. Run gold set tests in the evaluator

EXAMPLE phrases.json entry:
{
  "id": "en_001",
  "text": "Hello, my name is Bruce Garro",
  "language": "en",
  "source_video": "bruce_english.mp4",
  "start_time": 5.2,
  "end_time": 8.5,
  "duration": 3.3,
  "difficulty": "easy",
  "use_case": "greeting",
  "notes": "Clear greeting at start of video",
  "clip_path": "clips/en_001.mp4"
}

TIP: Use VLC or QuickTime to play videos and note timestamps.
      VLC shows timestamps in the bottom toolbar.
""")
    
    print("\n" + "=" * 70)
    
    # Ask if user wants to play a video to help identify phrases
    play = input("\nWould you like to play a source video now? (y/n): ").lower()
    
    if play == 'y':
        print("\nWhich video?")
        print("  1. bruce_english.mp4")
        print("  2. bruce_mandarin.mp4")
        print("  3. bruce_spanish.mp4")
        print("  4. bruce_expressive_motion.mp4")
        
        choice = input("Enter number (1-4): ")
        
        videos = {
            '1': '../assets/videos/bruce_english.mp4',
            '2': '../assets/videos/bruce_mandarin.mp4',
            '3': '../assets/videos/bruce_spanish.mp4',
            '4': '../assets/videos/bruce_expressive_motion.mp4'
        }
        
        if choice in videos:
            video_path = script_dir.parent.parent / videos[choice].replace('../', '')
            if video_path.exists():
                print(f"\nPlaying {video_path.name}...")
                print("Watch and note down phrases with timestamps!\n")
                play_video_segment(str(video_path))
            else:
                print(f"Video not found: {video_path}")
    
    print("\n" + "=" * 70)
    print("Next: Edit phrases_template.json with your phrases, then save as phrases.json")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    interactive_phrase_builder()
