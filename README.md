# Realtime Avatar: Multilingual AI Avatar System

Low-latency, multilingual conversational avatar with TensorRT acceleration, voice cloning, and realistic lip-sync animation.

## 🎯 Overview

**Status:** Phase 3 Complete ✅ | **Performance:** 2x RTF (near real-time)

Creates a digital avatar that:
- 🗣️ Speaks in **cloned voice** (EN/ZH/ES) using XTTS-v2
- 🎭 Animates from **single photo** using Ditto + TensorRT
- ⚡ **2x RTF** generation (1.95x RTF full pipeline)
- 💰 Scales to zero on Cloud Run GPU
- 🔧 Local dev (M3 Mac) + Cloud production (GCP L4)

## 🚀 Latest Performance (Nov 15, 2025)

**TensorRT Breakthrough:** 2.5x speedup over PyTorch!

| Component | RTF | Status |
|-----------|-----|--------|
| TTS (XTTS-v2) | **0.70x** | ⚡ Faster than realtime |
| Video (Ditto TRT) | **1.23x** | ⚡ Near realtime |
| **Full Pipeline** | **1.95x** | 🚀 Production ready |

**Concurrent Workers:** 3,685 videos/hour (2 workers on L4 GPU)

📊 [Full benchmarks →](PERFORMANCE.md)

## 🏗️ Architecture

**Ditto + TensorRT:** Audio-driven talking head synthesis
- HuBERT audio encoder + LMDM diffusion
- TensorRT optimized (2.5x speedup)
- Near real-time at 20.3 FPS

**Deployment:**
- **Local:** M3 Mac with MPS (5-10x faster than CPU)
- **Production:** GCP L4 GPU with TensorRT (2x RTF)

📖 [Setup guide →](SETUP.md)

## 🚀 Quick Start

### Local Development (M3 Mac)

```bash
# 1. Setup GPU service (MPS acceleration)
cd runtime && ./setup_gpu_service.sh && ./run_gpu_service.sh &

# 2. Extract voice samples
./scripts/extract_voice_samples.sh

# 3. Start runtime
docker compose up runtime

# 4. Generate video
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!", "language": "en"}'
```

### GCP L4 GPU (TensorRT)

```bash
# 1. Create instance
gcloud compute instances create realtime-avatar \
  --zone=us-east1-c --machine-type=g2-standard-4 \
  --accelerator=type=nvidia-l4,count=1 --boot-disk-size=200GB

# 2. Install drivers & deploy
# (See SETUP.md for complete instructions)

# 3. Test
curl -X POST http://INSTANCE_IP:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the cloud!", "language": "en"}'
```

📖 [Complete setup guide →](SETUP.md)

## 📊 API Examples

**Generate English video:**
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! This is a test.",
    "language": "en",
    "reference_image": "bruce_neutral.jpg"
  }'
```

**Generate Chinese video:**
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界！", "language": "zh-cn"}'
```

**Generate Spanish video:**
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "¡Hola mundo!", "language": "es"}'
```

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **TTS** | XTTS-v2 (multilingual voice cloning) |
| **Avatar** | Ditto + TensorRT (audio-driven animation) |
| **ASR** | Faster-Whisper (Phase 3) |
| **API** | FastAPI (Python async) |
| **Deployment** | Docker + GCP L4 GPU |

## 📂 Key Files

- `runtime/app.py` - FastAPI application
- `runtime/models/tts.py` - XTTS-v2 voice cloning
- `runtime/models/ditto_model.py` - Ditto avatar with TensorRT
- `runtime/gpu_service.py` - GPU acceleration service
- `runtime/pipelines/phase1_script.py` - Text → video pipeline
- `evaluator/run_evaluator.py` - Automated testing

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Complete setup guide (local + GCP)
- **[PERFORMANCE.md](PERFORMANCE.md)** - Benchmarks and optimization
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current development status
- **[docs/TENSORRT_SETUP.md](docs/TENSORRT_SETUP.md)** - TensorRT installation

## 🎯 Development Roadmap

- ✅ **Phase 1:** Script → video (GPU accelerated)
- ✅ **Phase 2:** Voice cloning + optimization
- ✅ **Phase 3:** TensorRT (2.5x speedup)
- 📅 **Phase 4:** Semi-interactive chat
- 📅 **Phase 5:** Real-time WebRTC streaming

---

**Last Updated:** November 16, 2025 | **Status:** Phase 3 Complete ✅
