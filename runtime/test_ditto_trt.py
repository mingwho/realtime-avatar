#!/usr/bin/env python3
"""
Test Ditto TensorRT inference and compare performance to PyTorch.
"""
import os
import sys
import time
import pickle
import numpy as np
import cv2
from pathlib import Path

# Add ditto to path
sys.path.insert(0, '/app/ditto-talkinghead')

def test_tensorrt_loading():
    """Test if TensorRT engines can be loaded."""
    print("=" * 80)
    print("Testing TensorRT Engine Loading")
    print("=" * 80)
    
    import tensorrt as trt
    print(f"TensorRT version: {trt.__version__}")
    
    engine_dir = Path("/app/ditto-talkinghead/checkpoints/ditto_trt_Ampere_Plus")
    if not engine_dir.exists():
        print(f"ERROR: Engine directory not found: {engine_dir}")
        return False
    
    engine_files = list(engine_dir.glob("*.engine"))
    print(f"\nFound {len(engine_files)} engine files:")
    for engine_file in sorted(engine_files):
        size_mb = engine_file.stat().st_size / (1024 * 1024)
        print(f"  - {engine_file.name} ({size_mb:.1f} MB)")
    
    # Test loading one engine
    print(f"\nTesting engine load: hubert_fp32.engine")
    test_engine = engine_dir / "hubert_fp32.engine"
    
    try:
        logger = trt.Logger(trt.Logger.WARNING)
        runtime = trt.Runtime(logger)
        
        with open(test_engine, 'rb') as f:
            engine_data = f.read()
        
        engine = runtime.deserialize_cuda_engine(engine_data)
        if engine:
            print(f"✓ Successfully loaded {test_engine.name}")
            print(f"  - Num bindings: {engine.num_bindings}")
            print(f"  - Max batch size: {engine.max_batch_size}")
            return True
        else:
            print(f"✗ Failed to deserialize engine")
            return False
            
    except Exception as e:
        print(f"✗ Error loading engine: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ditto_trt_inference():
    """Test full Ditto TensorRT inference pipeline."""
    print("\n" + "=" * 80)
    print("Testing Ditto TensorRT Inference")
    print("=" * 80)
    
    # Check if config file exists
    config_path = Path("/app/ditto-talkinghead/checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl")
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        return False
    
    print(f"Loading config: {config_path}")
    with open(config_path, 'rb') as f:
        config = pickle.load(f)
    
    print(f"Config keys: {list(config.keys())}")
    
    # Try to import Ditto modules
    try:
        print("\nImporting Ditto modules...")
        from ditto.inference import DittoInference
        print("✓ Successfully imported DittoInference")
    except ImportError as e:
        print(f"✗ Failed to import Ditto modules: {e}")
        print("\nAttempting alternative import...")
        try:
            # Try direct inference script
            sys.path.insert(0, '/app/ditto-talkinghead/ditto')
            from inference import DittoInference
            print("✓ Successfully imported DittoInference (alternative path)")
        except ImportError as e2:
            print(f"✗ Alternative import also failed: {e2}")
            return False
    
    # Initialize TRT model
    print("\nInitializing Ditto TensorRT model...")
    try:
        model = DittoInference(
            config_path=str(config_path),
            engine_dir="/app/ditto-talkinghead/checkpoints/ditto_trt_Ampere_Plus",
            device="cuda:0"
        )
        print("✓ Model initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize model: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Load test image
    test_image_path = "/app/runtime/bruce_haircut_cropped.jpg"
    if not Path(test_image_path).exists():
        print(f"ERROR: Test image not found: {test_image_path}")
        return False
    
    print(f"\nLoading test image: {test_image_path}")
    image = cv2.imread(test_image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print(f"Image shape: {image_rgb.shape}")
    
    # Generate dummy audio features (would come from TTS)
    print("\nGenerating dummy audio features...")
    audio_length_sec = 3.0  # 3 second test
    fps = 25
    num_frames = int(audio_length_sec * fps)
    # HuBERT features are typically 1024-dim
    audio_features = np.random.randn(num_frames, 1024).astype(np.float32)
    print(f"Audio features shape: {audio_features.shape}")
    
    # Run inference
    print(f"\nRunning TensorRT inference ({num_frames} frames)...")
    start_time = time.time()
    
    try:
        output_frames = model.inference(
            source_image=image_rgb,
            audio_features=audio_features
        )
        inference_time = time.time() - start_time
        
        print(f"✓ Inference completed successfully")
        print(f"  - Generated {len(output_frames)} frames")
        print(f"  - Total time: {inference_time:.3f}s")
        print(f"  - FPS: {len(output_frames) / inference_time:.2f}")
        print(f"  - RTF: {inference_time / audio_length_sec:.2f}x")
        
        return True
        
    except Exception as e:
        print(f"✗ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Ditto TensorRT Testing")
    print("=" * 80)
    print()
    
    # Test 1: TensorRT engine loading
    if not test_tensorrt_loading():
        print("\n❌ TensorRT engine loading failed")
        return 1
    
    # Test 2: Full inference pipeline
    if not test_ditto_trt_inference():
        print("\n❌ TensorRT inference failed")
        return 1
    
    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
