# Hybrid Avatar Backend Architecture

## Overview

The system supports **two avatar generation backends** optimized for different deployment environments:

- **SadTalker**: For local development on M3 Mac (MPS acceleration)
- **LivePortrait**: For cloud production on GCP (CUDA acceleration)

## Backend Comparison

| Feature | SadTalker | LivePortrait |
|---------|-----------|--------------|
| **Speed** | Moderate (~40-50s for 10s video) | Fast (~5-10s for 10s video) |
| **Quality** | Good, natural expressions | Excellent, state-of-the-art |
| **MPS Support** | ✅ Tested and working | ⚠️ Limited compatibility |
| **CUDA Support** | ✅ Works | ✅ Optimized |
| **Model Size** | Large (~2GB) | Medium (~500MB) |
| **Released** | 2022 | 2024 |
| **Use Case** | Local dev, fallback | Cloud production |

## Configuration

### Auto-Selection (Recommended)

Set `AVATAR_BACKEND=auto` and the system will automatically choose:
- **CUDA** → LivePortrait (optimal performance)
- **MPS/CPU** → SadTalker (compatibility)

### Manual Selection

Override the backend for specific use cases:

```bash
# Local development (M3 Mac)
AVATAR_BACKEND=sadtalker docker-compose up

# Cloud production (GCP L4)
AVATAR_BACKEND=liveportrait docker-compose up
```

## Setup

### 1. SadTalker (Already Installed)

SadTalker is already integrated in `runtime/SadTalker/`.

### 2. LivePortrait (For Cloud Deployment)

```bash
# Run setup script
./scripts/setup_liveportrait.sh

# Or manually
cd runtime
git clone https://github.com/KwaiVGI/LivePortrait.git
cd LivePortrait
pip install -r requirements.txt
python scripts/download_models.py
```

## Deployment Examples

### Local Development (M3 Mac)

```bash
# Use .env.local configuration
cp .env.local .env
docker-compose up

# Or explicit:
AVATAR_BACKEND=sadtalker docker-compose up
```

Backend: **SadTalker** on MPS  
Expected Performance: ~40-50s for 10s video

### Cloud Production (GCP L4)

```bash
# Use .env.cloud configuration
cp .env.cloud .env
docker-compose up

# Or explicit:
USE_CUDA=true AVATAR_BACKEND=liveportrait docker-compose up
```

Backend: **LivePortrait** on CUDA  
Expected Performance: ~5-10s for 10s video (5-10x faster!)

## Health Check

Check which backend is running:

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "device": "cuda",
  "avatar_backend": "liveportrait",
  "models": {
    "tts": true,
    "avatar": true,
    "avatar_backend": "liveportrait"
  }
}
```

## Fallback Behavior

If LivePortrait fails to load on CUDA (missing dependencies, etc.), the system automatically falls back to SadTalker:

```
2025-11-09 20:00:00 - ERROR - Failed to load LivePortrait: ...
2025-11-09 20:00:01 - INFO - Falling back to SadTalker...
2025-11-09 20:00:15 - INFO - ✅ SadTalker model ready (fallback)
```

## Files

- `runtime/models/sadtalker_model.py` - SadTalker wrapper
- `runtime/models/liveportrait_model.py` - LivePortrait wrapper
- `runtime/gpu_service.py` - Unified GPU service with backend selection
- `runtime/Dockerfile.gpu-service` - GPU service container with both backends
- `.env.local` - Local development configuration
- `.env.cloud` - Cloud production configuration
- `scripts/setup_liveportrait.sh` - LivePortrait setup script

## Performance Targets

### Local (M3 Mac + MPS)
- TTS: ~5s for 5s audio
- Avatar (SadTalker): ~40-50s for 10s video
- **Total: ~45-55s**

### Cloud (L4 GPU + CUDA)
- TTS: ~3s for 5s audio (1.5x faster)
- Avatar (LivePortrait): ~5-10s for 10s video (5-10x faster!)
- **Total: ~8-13s** (4-6x overall speedup!)

## Troubleshooting

### LivePortrait not loading on CUDA

1. Check model weights are downloaded:
   ```bash
   ls -la runtime/LivePortrait/pretrained_weights/
   ```

2. Verify CUDA is available:
   ```bash
   docker exec realtime-avatar-gpu python -c "import torch; print(torch.cuda.is_available())"
   ```

3. Check logs:
   ```bash
   docker logs realtime-avatar-gpu
   ```

### SadTalker on MPS issues

1. Ensure PyTorch MPS fallback is enabled:
   ```bash
   echo $PYTORCH_ENABLE_MPS_FALLBACK  # Should be "1"
   ```

2. Check SadTalker patches applied:
   ```bash
   cd runtime
   python patch_sadtalker.py
   ```

## Next Steps

- [ ] Benchmark LivePortrait on L4 GPU
- [ ] Compare quality: SadTalker vs LivePortrait
- [ ] Add Wav2Lip for post-processing lip sync
- [ ] Implement video quality metrics
