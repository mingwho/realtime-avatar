#!/usr/bin/env python3
"""
Benchmark Ditto TensorRT inference vs PyTorch.
Uses official Ditto API (StreamSDK) with TensorRT engines.
"""
import os
import sys
import time
import librosa
import math
import pickle
import argparse
from pathlib import Path

# Add ditto to path
sys.path.insert(0, '/app/ditto-talkinghead')

from stream_pipeline_offline import StreamSDK


def benchmark_trt_inference(
    cfg_pkl: str,
    data_root: str,
    audio_path: str,
    source_path: str,
    output_path: str
):
    """
    Run Ditto TensorRT inference and measure performance.
    
    Args:
        cfg_pkl: Path to TRT config pickle
        data_root: Path to TRT engine directory
        audio_path: Path to input audio file
        source_path: Path to input image
        output_path: Path to output video
    
    Returns:
        dict with timing metrics
    """
    print("=" * 80)
    print("Ditto TensorRT Benchmark")
    print("=" * 80)
    
    print(f"\nConfig: {cfg_pkl}")
    print(f"Engines: {data_root}")
    print(f"Audio: {audio_path}")
    print(f"Image: {source_path}")
    print(f"Output: {output_path}")
    
    # Initialize SDK
    print("\nInitializing StreamSDK with TensorRT engines...")
    init_start = time.time()
    SDK = StreamSDK(cfg_pkl, data_root)
    init_time = time.time() - init_start
    print(f"✓ SDK initialized in {init_time:.2f}s")
    
    # Load and analyze audio
    print("\nLoading audio...")
    audio, sr = librosa.core.load(audio_path, sr=16000)
    audio_duration = len(audio) / sr
    num_frames = math.ceil(len(audio) / 16000 * 25)
    print(f"  Audio duration: {audio_duration:.2f}s")
    print(f"  Expected frames: {num_frames} @ 25fps")
    
    # Setup inference
    print("\nSetting up inference...")
    setup_start = time.time()
    SDK.setup(source_path, output_path)
    SDK.setup_Nd(N_d=num_frames, fade_in=-1, fade_out=-1, ctrl_info={})
    setup_time = time.time() - setup_start
    print(f"✓ Setup complete in {setup_time:.2f}s")
    
    # Run inference
    print(f"\nRunning TensorRT inference...")
    print(f"  Processing {num_frames} frames ({audio_duration:.2f}s audio)")
    inference_start = time.time()
    
    # Extract features and run
    aud_feat = SDK.wav2feat.wav2feat(audio)
    SDK.audio2motion_queue.put(aud_feat)
    SDK.close()
    
    inference_time = time.time() - inference_start
    print(f"✓ Inference complete in {inference_time:.2f}s")
    
    # Mux audio and video
    print("\nMuxing audio and video with ffmpeg...")
    mux_start = time.time()
    cmd = f'ffmpeg -loglevel error -y -i "{SDK.tmp_output_path}" -i "{audio_path}" -map 0:v -map 1:a -c:v copy -c:a aac "{output_path}"'
    os.system(cmd)
    mux_time = time.time() - mux_start
    print(f"✓ Muxing complete in {mux_time:.2f}s")
    
    # Calculate metrics
    total_time = init_time + setup_time + inference_time + mux_time
    rtf = inference_time / audio_duration
    fps = num_frames / inference_time
    
    print("\n" + "=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    print(f"Initialization:  {init_time:8.2f}s")
    print(f"Setup:           {setup_time:8.2f}s")
    print(f"Inference:       {inference_time:8.2f}s")
    print(f"Muxing:          {mux_time:8.2f}s")
    print(f"Total:           {total_time:8.2f}s")
    print("-" * 80)
    print(f"Audio duration:  {audio_duration:8.2f}s")
    print(f"Frames:          {num_frames:8d}")
    print(f"FPS:             {fps:8.2f}")
    print(f"RTF:             {rtf:8.2f}x")
    print("=" * 80)
    
    if rtf < 1.0:
        print("🎉 REAL-TIME CAPABLE! (RTF < 1.0)")
    elif rtf < 1.5:
        print("✓ Near real-time (RTF < 1.5)")
    elif rtf < 2.0:
        print("○ Acceptable for pre-recording (RTF < 2.0)")
    else:
        print("⚠ Slower than desired (RTF > 2.0)")
    
    print(f"\nOutput saved to: {output_path}")
    
    return {
        "init_time": init_time,
        "setup_time": setup_time,
        "inference_time": inference_time,
        "mux_time": mux_time,
        "total_time": total_time,
        "audio_duration": audio_duration,
        "num_frames": num_frames,
        "fps": fps,
        "rtf": rtf
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark Ditto TensorRT inference")
    parser.add_argument(
        "--data_root",
        type=str,
        default="/app/ditto-talkinghead/checkpoints/ditto_trt_Ampere_Plus",
        help="Path to TensorRT engines"
    )
    parser.add_argument(
        "--cfg_pkl",
        type=str,
        default="/app/ditto-talkinghead/checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl",
        help="Path to TRT config pickle"
    )
    parser.add_argument(
        "--audio_path",
        type=str,
        required=True,
        help="Path to input audio file (.wav)"
    )
    parser.add_argument(
        "--source_path",
        type=str,
        required=True,
        help="Path to input image"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="/app/runtime/output_trt.mp4",
        help="Path to output video"
    )
    
    args = parser.parse_args()
    
    # Verify files exist
    for path, name in [(args.cfg_pkl, "config"), (args.data_root, "engines"), 
                       (args.audio_path, "audio"), (args.source_path, "image")]:
        if not Path(path).exists():
            print(f"ERROR: {name} not found: {path}")
            return 1
    
    # Run benchmark
    try:
        metrics = benchmark_trt_inference(
            cfg_pkl=args.cfg_pkl,
            data_root=args.data_root,
            audio_path=args.audio_path,
            source_path=args.source_path,
            output_path=args.output_path
        )
        
        print("\n✅ Benchmark completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
