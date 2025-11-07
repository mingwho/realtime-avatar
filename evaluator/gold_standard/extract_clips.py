#!/usr/bin/env python3
"""
Extract video clips from source videos based on phrases.json timestamps.

Usage:
    python extract_clips.py
    
This will read phrases.json and extract clips from the source videos
into the clips/ directory.
"""

import json
import subprocess
import os
from pathlib import Path

def extract_clip(source_video: str, start_time: float, end_time: float, output_path: str):
    """
    Extract a clip from a video using ffmpeg.
    
    Args:
        source_video: Path to source video file
        start_time: Start timestamp in seconds
        end_time: End timestamp in seconds
        output_path: Path for output clip
    """
    duration = end_time - start_time
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-ss', str(start_time),  # Start time
        '-i', source_video,  # Input video
        '-t', str(duration),  # Duration
        '-c:v', 'libx264',  # Video codec
        '-c:a', 'aac',  # Audio codec
        '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
        output_path
    ]
    
    print(f"Extracting: {output_path}")
    print(f"  Source: {source_video}")
    print(f"  Time: {start_time:.2f}s - {end_time:.2f}s ({duration:.2f}s)")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  ❌ Error: {result.stderr}")
        return False
    else:
        print(f"  ✅ Success!")
        return True

def main():
    """Extract all clips defined in phrases.json"""
    
    # Load phrases configuration
    script_dir = Path(__file__).parent
    phrases_file = script_dir / 'phrases.json'
    
    if not phrases_file.exists():
        print("❌ phrases.json not found!")
        print("   Copy phrases_template.json to phrases.json and fill in your data.")
        return
    
    with open(phrases_file, 'r') as f:
        config = json.load(f)
    
    print(f"📋 Found {len(config['phrases'])} phrases to extract\n")
    
    # Get base path for assets
    assets_base = script_dir.parent.parent / 'assets' / 'videos'
    
    success_count = 0
    fail_count = 0
    
    for phrase in config['phrases']:
        # Check if placeholder text
        if phrase['text'] == 'REPLACE_WITH_ACTUAL_TEXT':
            print(f"⚠️  Skipping {phrase['id']}: Text not filled in yet")
            continue
        
        # Construct paths
        source_path = assets_base / phrase['source_video']
        output_path = script_dir / phrase['clip_path']
        
        if not source_path.exists():
            print(f"❌ Source video not found: {source_path}")
            fail_count += 1
            continue
        
        # Extract clip
        if extract_clip(
            str(source_path),
            phrase['start_time'],
            phrase['end_time'],
            str(output_path)
        ):
            success_count += 1
        else:
            fail_count += 1
        
        print()  # Blank line between clips
    
    print("=" * 60)
    print(f"✅ Successfully extracted: {success_count} clips")
    print(f"❌ Failed: {fail_count} clips")
    print(f"📁 Clips saved to: {script_dir / 'clips'}")
    print("=" * 60)

if __name__ == '__main__':
    main()
