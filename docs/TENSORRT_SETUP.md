# TensorRT Setup Guide for Ditto

This guide documents the successful installation and configuration of TensorRT 8.6.1 with Ditto for 2.5x performance improvement.

## Performance Improvements

**Before (PyTorch):**
- 3.07x RTF @ 384x579 resolution, 25 diffusion steps
- 8.15 FPS processing speed

**After (TensorRT):**
- **1.23x RTF** @ 384x579 resolution, 25 diffusion steps ⚡⚡
- **20.3 FPS** processing speed
- **2.5x speedup** over PyTorch baseline!

## Prerequisites

- CUDA 12.1 (must be installed system-wide)
- Python 3.10
- NVIDIA GPU with Compute Capability ≥ 7.5 (Ampere or newer recommended)
- Ubuntu 22.04 (tested environment)

## Installation Steps

### 1. Fix Python Symlink

Ensure `/usr/bin/python3` points to Python 3.10:

```bash
ls -la /usr/bin/python3
# If not pointing to python3.10:
sudo rm /usr/bin/python3
sudo ln -s /usr/bin/python3.10 /usr/bin/python3
```

### 2. Install TensorRT Libraries

Install tensorrt-libs first (system Python, no venv):

```bash
/usr/bin/python3 -m pip install tensorrt-libs==8.6.1 \
  --index-url https://pypi.nvidia.com
```

### 3. Install TensorRT (No Build Isolation)

Critical: Use `--no-build-isolation` to avoid compilation issues:

```bash
/usr/bin/python3 -m pip install \
  --no-build-isolation \
  tensorrt==8.6.1
```

### 4. Install CUDA Python Bindings

```bash
/usr/bin/python3 -m pip install cuda-python==12.8.0
```

### 5. Fix NumPy Compatibility

Ditto requires NumPy ≥1.24 for `np.arctan2`, but older Ditto code uses deprecated `np.atan2`:

```bash
# Find the mediapipe file
find /app -name "mediapipe_landmark478.py" 2>/dev/null

# Patch the deprecated function
sed -i 's/np.atan2/np.arctan2/g' \
  /app/ditto-talkinghead/core/aux_models/mediapipe_landmark478.py

# Install compatible NumPy
pip install numpy==1.24.3
```

### 6. Verify Installation

```python
python3 -c "import tensorrt; print(f'TensorRT version: {tensorrt.__version__}')"
python3 -c "import cuda; print('CUDA Python: OK')"
```

Expected output:
```
TensorRT version: 8.6.1.6
CUDA Python: OK
```

## Download Pre-built TensorRT Engines

Ditto provides official pre-built TensorRT engines on HuggingFace:

```bash
cd /app/ditto-talkinghead/checkpoints
git clone https://huggingface.co/WangZeJun/ditto_trt_Ampere_Plus

# Verify engines (should be ~1.9GB total)
ls -lh ditto_trt_Ampere_Plus/*.trt
```

Engines included:
- `appearance_extractor.trt`
- `decoder.trt`
- `hubert.trt`
- `lmdm_1.trt` through `lmdm_4.trt`
- `motion_extractor.trt`
- `vae_decoder.trt`
- `vae_encoder.trt`

## Configuration

### Optimize Diffusion Steps

Edit the TensorRT config to reduce diffusion steps for speed:

```bash
vim /app/ditto-talkinghead/checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl
```

Modify `sampling_timesteps` from 50 → 25 for 2x speedup with minimal quality loss.

## Usage

### Benchmark Script

Use the provided benchmark script:

```bash
python3 /app/runtime/benchmark_ditto_trt.py \
  --source_path /path/to/image.jpg \
  --audio_path /path/to/audio.wav \
  --output_path output_video.mp4
```

### Complete Voice Cloning Pipeline

For text-to-speech + lip sync:

```bash
python3 /root/complete_pipeline.py \
  --text "Your text here" \
  --speaker /path/to/voice_sample.wav \
  --image /path/to/portrait.jpg \
  --output video_output.mp4 \
  --language en
```

## Troubleshooting

### Issue: TensorRT not found
**Error:** `ModuleNotFoundError: No module named 'tensorrt'`

**Solution:** Install with system Python, not in venv:
```bash
/usr/bin/python3 -m pip install tensorrt-libs==8.6.1 --index-url https://pypi.nvidia.com
/usr/bin/python3 -m pip install --no-build-isolation tensorrt==8.6.1
```

### Issue: Build dependencies failed
**Error:** Multiple compilation errors during pip install

**Solution:** Use `--no-build-isolation` flag to skip building wheels.

### Issue: NumPy atan2 not found
**Error:** `AttributeError: module 'numpy' has no attribute 'atan2'`

**Solution:** Replace `np.atan2` with `np.arctan2` in mediapipe file (see step 5).

### Issue: CUDA Python import error
**Error:** `ImportError: cannot import name 'cuda' from 'cuda'`

**Solution:** Install cuda-python:
```bash
pip install cuda-python==12.8.0
```

### Issue: Wrong TensorRT version
**Error:** Engine built for TensorRT 8.6.1 but found 10.x

**Solution:** Uninstall all tensorrt packages and reinstall from NVIDIA PyPI index:
```bash
pip uninstall -y tensorrt tensorrt-libs tensorrt-bindings
/usr/bin/python3 -m pip install tensorrt-libs==8.6.1 --index-url https://pypi.nvidia.com
/usr/bin/python3 -m pip install --no-build-isolation tensorrt==8.6.1
```

## Performance Optimization Tips

1. **Resolution:** 384x579 gives best speed/quality balance
2. **Diffusion Steps:** 25 steps is optimal (50% faster than 50 steps)
3. **Batch Processing:** Keep models loaded between runs
4. **Memory:** TensorRT uses ~5GB VRAM (vs 7GB for PyTorch)

## Known Limitations

1. **NumPy Conflicts:** TTS (requires 1.22.0) vs Ditto (requires 1.24.3)
   - Solution: Run TTS in separate process (see `complete_pipeline.py`)

2. **CUDA Version:** Must use CUDA 12.1 (engines are compiled for specific CUDA version)

3. **GPU Compatibility:** Pre-built engines are for Ampere+ (RTX 30xx, A100, L4, etc.)

## Additional Resources

- [Ditto GitHub](https://github.com/OpenTalker/Ditto)
- [TensorRT Documentation](https://docs.nvidia.com/deeplearning/tensorrt/)
- [NVIDIA PyPI Index](https://pypi.nvidia.com)
