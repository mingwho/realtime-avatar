#!/usr/bin/env python3
"""
Complete end-to-end TensorRT pipeline:
1. Text -> TTS (audio generation)
2. Audio -> Ditto TensorRT (lip-synced video)
"""
import os
import sys
import time
import librosa
import math
import argparse
from pathlib import Path

# Add ditto to path
sys.path.insert(0, '/app/ditto-talkinghead')
from stream_pipeline_offline import StreamSDK


def generate_audio_with_tts(text: str, output_path: str, voice: str = "default") -> dict:
    """
    Generate audio from text using TTS.
    
    Args:
        text: Input text to synthesize
        output_path: Path to save audio file
        voice: Voice model to use
    
    Returns:
        dict with audio generation metrics
    """
    print("=" * 80)
    print("Step 1: Text-to-Speech")
    print("=" * 80)
    print(f"Text: {text}")
    print(f"Output: {output_path}")
    
    tts_start = time.time()
    
    # Import TTS
    from TTS.api import TTS
    
    # Initialize TTS model
    print("\nInitializing TTS model...")
    tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False)
    
    # Generate speech
    print("Generating speech...")
    tts.tts_to_file(
        text=text,
        file_path=output_path,
        speaker="p326"  # Female voice
    )
    
    tts_time = time.time() - tts_start
    
    # Get audio duration
    audio, sr = librosa.core.load(output_path, sr=16000)
    audio_duration = len(audio) / sr
    
    print(f"✓ Audio generated in {tts_time:.2f}s")
    print(f"  Audio duration: {audio_duration:.2f}s")
    print(f"  Real-time factor: {tts_time / audio_duration:.2f}x")
    
    return {
        "tts_time": tts_time,
        "audio_duration": audio_duration,
        "audio_path": output_path,
        "rtf": tts_time / audio_duration
    }


def run_ditto_trt(
    cfg_pkl: str,
    data_root: str,
    audio_path: str,
    source_path: str,
    output_path: str
) -> dict:
    """
    Run Ditto TensorRT inference for lip syncing.
    
    Args:
        cfg_pkl: Path to TRT config pickle
        data_root: Path to TRT engine directory
        audio_path: Path to input audio file
        source_path: Path to input image
        output_path: Path to output video
    
    Returns:
        dict with timing metrics
    """
    print("\n" + "=" * 80)
    print("Step 2: Lip Sync with Ditto TensorRT")
    print("=" * 80)
    
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
    print("\nMuxing audio and video...")
    mux_start = time.time()
    cmd = f'ffmpeg -loglevel error -y -i "{SDK.tmp_output_path}" -i "{audio_path}" -map 0:v -map 1:a -c:v copy -c:a aac "{output_path}"'
    os.system(cmd)
    mux_time = time.time() - mux_start
    print(f"✓ Muxing complete in {mux_time:.2f}s")
    
    # Calculate metrics
    total_time = init_time + setup_time + inference_time + mux_time
    rtf = inference_time / audio_duration
    fps = num_frames / inference_time
    
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
    parser = argparse.ArgumentParser(description="Complete TTS + TensorRT pipeline")
    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="Input text to synthesize"
    )
    parser.add_argument(
        "--source_image",
        type=str,
        default="/app/runtime/bruce_haircut_small.jpg",
        help="Path to input image"
    )
    parser.add_argument(
        "--output_video",
        type=str,
        default="/app/runtime/output_complete.mp4",
        help="Path to output video"
    )
    parser.add_argument(
        "--audio_output",
        type=str,
        default="/app/runtime/generated_audio.wav",
        help="Path to save generated audio"
    )
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
    
    args = parser.parse_args()
    
    # Verify source image exists
    if not Path(args.source_image).exists():
        print(f"ERROR: Source image not found: {args.source_image}")
        return 1
    
    print("=" * 80)
    print("COMPLETE END-TO-END PIPELINE: Text -> TTS -> Lip Sync")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Generate audio from text
        tts_metrics = generate_audio_with_tts(
            text=args.text,
            output_path=args.audio_output
        )
        
        # Step 2: Run Ditto TensorRT for lip syncing
        ditto_metrics = run_ditto_trt(
            cfg_pkl=args.cfg_pkl,
            data_root=args.data_root,
            audio_path=args.audio_output,
            source_path=args.source_image,
            output_path=args.output_video
        )
        
        # Print complete pipeline metrics
        print("\n" + "=" * 80)
        print("COMPLETE PIPELINE METRICS")
        print("=" * 80)
        
        total_pipeline_time = tts_metrics["tts_time"] + ditto_metrics["total_time"]
        audio_duration = tts_metrics["audio_duration"]
        
        print("\n--- TTS Metrics ---")
        print(f"Generation time: {tts_metrics['tts_time']:8.2f}s")
        print(f"TTS RTF:         {tts_metrics['rtf']:8.2f}x")
        
        print("\n--- Lip Sync Metrics ---")
        print(f"Initialization:  {ditto_metrics['init_time']:8.2f}s")
        print(f"Setup:           {ditto_metrics['setup_time']:8.2f}s")
        print(f"Inference:       {ditto_metrics['inference_time']:8.2f}s")
        print(f"Muxing:          {ditto_metrics['mux_time']:8.2f}s")
        print(f"Lip Sync RTF:    {ditto_metrics['rtf']:8.2f}x")
        
        print("\n--- Pipeline Total ---")
        print(f"Total time:      {total_pipeline_time:8.2f}s")
        print(f"Audio duration:  {audio_duration:8.2f}s")
        print(f"Overall RTF:     {total_pipeline_time / audio_duration:8.2f}x")
        print("=" * 80)
        
        overall_rtf = total_pipeline_time / audio_duration
        if overall_rtf < 1.0:
            print("🎉 REAL-TIME CAPABLE! (RTF < 1.0)")
        elif overall_rtf < 1.5:
            print("✓ Near real-time (RTF < 1.5)")
        elif overall_rtf < 2.0:
            print("○ Acceptable for pre-recording (RTF < 2.0)")
        else:
            print("⚠ Slower than desired (RTF > 2.0)")
        
        print(f"\nFinal video: {args.output_video}")
        print("✅ Complete pipeline finished successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
