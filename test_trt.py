#!/usr/bin/env python3
"""
🚀 TESTING: TensorRT Optimized Ditto (Official)
Testing the official TensorRT engines from Hugging Face
"""

import sys
import time
import os
import librosa
import math
import numpy as np
sys.path.append('/app/ditto-talkinghead')

from stream_pipeline_offline import StreamSDK

print("=" * 60)
print("🚀 TESTING: TensorRT Optimized Ditto")
print("=" * 60)
print()
print("Configuration:")
print("  Engine: TensorRT (ditto_trt_Ampere_Plus)")
print("  Config: v0.4_hubert_cfg_trt.pkl")
print("  Image: bruce_haircut_cropped.jpg (384x579px)")
print("  Hardware: L4 GPU (Ampere architecture)")
print()

# Initialize with TensorRT
print("Initializing TensorRT pipeline...")
init_start = time.time()

cfg_pkl = "/app/ditto-talkinghead/checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl"
data_root = "/app/ditto-talkinghead/checkpoints/ditto_trt_Ampere_Plus"
sdk = StreamSDK(cfg_pkl, data_root)

init_time = time.time() - init_start
print(f"✓ Initialization: {init_time:.2f}s")
print()

# Test input
image_path = "/tmp/bruce_haircut_cropped.jpg"
audio_path = "/tmp/test_audio.wav"
output_path = "/tmp/test_trt_video.mp4"
tmp_output = "/tmp/test_trt_video_tmp.mp4"

# Create test audio (using TTS from runtime container)
text = "Hello! This is a test of the TensorRT optimized Ditto model. Let's see how much faster it runs compared to the PyTorch version."
print(f"Input text: '{text}'")
print(f"Text length: {len(text)} characters")
print()

# Generate TTS
print("Generating TTS audio...")
tts_start = time.time()
os.system(f'cd /app/runtime && python -c "from models.tts import TTSModel; tts = TTSModel(); tts.generate(\'{text}\', \'{audio_path}\')" 2>/dev/null')
tts_time = time.time() - tts_start
print(f"✓ TTS completed: {tts_time:.2f}s")

# Get audio duration
audio, sr = librosa.core.load(audio_path, sr=16000)
audio_duration = len(audio) / 16000
print(f"✓ Audio duration: {audio_duration:.1f}s")
print()

# Generate video
print("Generating video with TensorRT...")
ditto_start = time.time()

# Setup
sdk.setup(image_path, tmp_output)
num_f = math.ceil(len(audio) / 16000 * 25)
sdk.setup_Nd(N_d=num_f)

# Process audio
aud_feat = sdk.wav2feat.wav2feat(audio)
sdk.audio2motion_queue.put(aud_feat)
sdk.close()

# Add audio to video
os.system(f'ffmpeg -loglevel error -y -i "{tmp_output}" -i "{audio_path}" -map 0:v -map 1:a -c:v copy -c:a aac "{output_path}"')

ditto_time = time.time() - ditto_start
print(f"✓ Video generation completed: {ditto_time:.2f}s")
print()

# Calculate metrics
total_time = tts_time + ditto_time
rtf = total_time / audio_duration
throughput = 3600 / total_time

print("=" * 60)
print("📊 PERFORMANCE RESULTS")
print("=" * 60)
print(f"TTS Time:        {tts_time:6.2f}s")
print(f"Ditto Time:      {ditto_time:6.2f}s")
print(f"Total Time:      {total_time:6.2f}s")
print(f"Audio Duration:  {audio_duration:6.1f}s")
print()
print(f"🎯 RTF (Real-Time Factor): {rtf:.2f}x")
print(f"📈 Throughput: {throughput:.0f} videos/hour")
print()

# Get video info
import subprocess
result = subprocess.run(
    ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
     '-show_entries', 'stream=width,height,r_frame_rate,nb_frames',
     '-show_entries', 'format=size',
     '-of', 'default=noprint_wrappers=1', output_path],
    capture_output=True, text=True
)

print("Video Details:")
for line in result.stdout.strip().split('\n'):
    if '=' in line:
        key, value = line.split('=')
        print(f"  {key}: {value}")
print()

# Compare with PyTorch baseline
baseline_rtf = 3.07  # Our best PyTorch result (384x579px, 25 steps)
speedup = baseline_rtf / rtf

print("=" * 60)
print("🔥 COMPARISON WITH PYTORCH")
print("=" * 60)
print(f"PyTorch RTF:     {baseline_rtf:.2f}x")
print(f"TensorRT RTF:    {rtf:.2f}x")
print(f"Speedup:         {speedup:.2f}x faster")
print()

if rtf < 1.0:
    print("🎉🎉🎉 REAL-TIME ACHIEVED! RTF < 1.0x 🎉🎉🎉")
    print(f"We are {1.0/rtf:.1f}x FASTER than real-time!")
elif rtf < 1.5:
    print("🎊 NEARLY REAL-TIME! Just {:.1f}% slower".format((rtf - 1.0) * 100))
else:
    print(f"⚠️  Still {rtf:.2f}x slower than real-time")
    print(f"Need {rtf:.2f}x more speedup to reach <1.0x RTF")

print()
print(f"Output saved to: {output_path}")
print("=" * 60)
