# Realtime Avatar: Multilingual Conversational Avatar System

A low-latency, multilingual conversational avatar system with TensorRT acceleration that generates realistic talking-head videos using voice cloning and AI animation.

## 🎯 Project Overview

**Current Phase**: Phase 3 (TensorRT Optimization) ✅ **COMPLETE**  
**Performance**: **Near real-time** video generation with TensorRT on L4 GPU

This system creates a digital avatar that:
- 🗣️ Speaks in cloned voice (multilingual: EN/ZH/ES) with XTTS-v2
- 🎭 Animates from reference images using **Ditto + TensorRT**
- ⚡ **Near real-time** generation: **1.23x RTF** (2.5x faster than PyTorch!)
- 💰 Scales to zero cost when idle (Cloud Run GPU)
- 🔧 Supports local development and cloud production (GCP L4 GPU)

## 🚀 Latest: TensorRT Integration (Nov 15, 2025)

**Major Performance Breakthrough:**
- **PyTorch Baseline:** 3.07x RTF
- **TensorRT Optimized:** **1.23x RTF** (20.3 FPS) ⚡⚡
- **Speedup:** **2.5x faster!**

**Complete Voice Cloning Pipeline:**
- Text → XTTS-v2 synthesis: **0.70x RTF** (faster than real-time)
- Audio → Ditto TensorRT lip sync: **1.25x RTF** (near real-time)
- End-to-end: **1.95x RTF** (excluding model loading)

See [TensorRT Setup Guide](docs/TENSORRT_SETUP.md) for installation instructions.

## 🎬 Avatar Technology: Ditto

**Ditto** (antgroup/ditto-talkinghead) - Audio-driven talking head synthesis framework:
- Built on LivePortrait components (appearance extraction, motion, warping)
- HuBERT audio encoder for speech analysis
- LMDM diffusion model for motion generation
- **TensorRT optimized** for near real-time performance
- High-quality output at 512x682 resolution (3:4 portrait)

## 📊 Performance

### TensorRT Optimized (L4 GPU)
| Component | RTF | Speed | Status |
|-----------|-----|-------|--------|
| XTTS-v2 TTS | **0.70x** | Faster than realtime | ⚡ |
| Ditto TensorRT | **1.23x** | Near realtime (20.3 FPS) | ⚡⚡ |
| Combined Pipeline | **1.95x** | Excluding model loading | 🚀 |

**Speedup:** 2.5x faster than PyTorch baseline (3.07x → 1.23x RTF)

### Historical Performance
| Metric | CPU Only | M3 MPS | L4 PyTorch | L4 TensorRT |
|--------|----------|---------|------------|-------------|
| TTS (XTTS-v2) | ~126s | ~2.4s | **0.72x** | **0.70x** |
| Avatar (Ditto) | N/A | N/A | 3.07x | **1.23x** ⚡⚡ |
| Total RTF | 27x | N/A | 3.79x | **1.95x** |

## 📋 Development Phases

- **Phase 1** ✅ **COMPLETE**: Script → Pre-rendered video (GPU accelerated)
- **Phase 2** ✅ **COMPLETE**: Voice cloning + optimization
- **Phase 3** ✅ **COMPLETE**: TensorRT integration (2.5x speedup!)
- **Phase 4** � (Next): Semi-interactive chat with response clips
- **Phase 5** 📅 (Future): Real-time WebRTC streaming conversation

## 🏗️ Architecture

```
┌──────────────────────────────────────┐
│  GPU Service (CUDA, Port 8001)       │
│  - XTTS-v2 TTS with voice cloning   │
│  - Ditto Avatar + TensorRT          │
│  - Faster-Whisper ASR               │
└──────────────┬───────────────────────┘
               │ HTTP API
┌──────────────▼───────────────────────┐
│  Runtime Service (Docker, Port 8000) │
│  - FastAPI orchestration             │
│  - Business logic                    │
│  - Asset management                  │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  Evaluator (Automated Testing)       │
│  - Test scenarios                    │
│  - Performance metrics               │
└──────────────────────────────────────┘
```

### Avatar Backends
- **Ditto + TensorRT** (default): Audio-driven, near real-time, 2.5x faster
- **Ditto PyTorch**: Fallback option, good quality but slower
- **SadTalker**: Alternative backend, MPS compatible

### Deployment Modes
- **Local Dev**: Docker runtime + native GPU service
- **Production**: GCP L4 GPU instance with TensorRT optimization

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- ffmpeg
- NVIDIA GPU with CUDA 12.1+ (for TensorRT) or macOS M1/M2/M3 (for MPS)

### Complete Voice Cloning Pipeline (TensorRT)

Generate a video with your cloned voice in near real-time:

```bash
# 1. Upload your voice sample (30+ seconds recommended)
gcloud compute scp your_voice.m4a instance:~/
docker cp instance:~/your_voice.m4a container:/root/

# 2. Convert to WAV format
docker exec container ffmpeg -i /root/your_voice.m4a \
  -ar 22050 -ac 1 /root/voice_sample.wav

# 3. Run complete pipeline
docker exec container python3 /root/complete_pipeline.py \
  --text "Your text to speak here" \
  --speaker /root/voice_sample.wav \
  --image /path/to/portrait.jpg \
  --output /root/output.mp4 \
  --language en

# 4. Download result
gcloud compute scp instance:~/output.mp4 ~/Downloads/
```

**Performance:** ~1.95x RTF for complete text → cloned speech → lip-synced video!

See [TensorRT Setup Guide](docs/TENSORRT_SETUP.md) for detailed installation instructions.
### Local Development (with GPU Acceleration)

1. **Setup GPU service** (for M3 Macs):
```bash
cd runtime
./setup_gpu_service.sh
./run_gpu_service.sh  # Runs in background on port 8001
```

2. **Extract voice samples**:
```bash
./scripts/extract_voice_samples.sh
```

3. **Build Docker images**:
```bash
./scripts/build_images.sh
```

4. **Start runtime service**:
```bash
docker compose up runtime  # Automatically connects to GPU service
```

5. **Test generation**:
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from GPU acceleration!", "language": "en"}'
```

6. **Run evaluator** (optional):
```bash
docker compose --profile evaluator up evaluator
```

Or use the all-in-one setup script:
```bash
./scripts/setup_local.sh
```

### Without GPU (CPU only)

Set `USE_EXTERNAL_GPU_SERVICE=false` in `docker-compose.yml` to run TTS in Docker (slower).

## 📁 Project Structure

```
realtime-avatar/
├── assets/                  # Reference media
│   ├── images/             # Avatar reference images
│   ├── videos/             # Reference motion videos
│   └── voice/              # Voice samples for cloning
├── runtime/                 # Main inference service
│   ├── models/             # Model wrappers (TTS, Avatar, ASR, LLM)
│   │   └── tts_client.py   # GPU service client
│   ├── pipelines/          # Generation pipelines
│   ├── utils/              # Utilities
│   ├── gpu_service.py      # GPU acceleration service (NEW)
│   ├── GPU_SERVICE.md      # GPU service documentation
│   └── app.py              # FastAPI application
├── evaluator/              # Testing & metrics
│   ├── scenarios/          # Test scenarios
│   ├── metrics/            # Metric calculators
│   └── run_evaluator.py    # Main runner
├── web/                    # React UI (stub)
├── infrastructure/         # Terraform (stub)
└── scripts/                # Utility scripts
```

## 🔬 Testing & Evaluation

The evaluator runs automated tests and generates metrics:
- ✅ English short/medium utterances
- ✅ Chinese (Mandarin) short/medium
- ✅ Spanish short/medium
- ✅ Language switching (EN→ZH, EN→ES, EN→ZH→ES)

### Metrics Collected
- **Latency**: TTS time, avatar rendering time, total time
- **Voice Quality**: Speaker similarity, F0/pitch analysis
- **Language**: Detection accuracy, correctness
- **Lip Sync**: Audio-video coherence (basic heuristic)

### Run Evaluator
```bash
docker compose --profile evaluator up evaluator
```

Results are saved to `evaluator/outputs/` as JSON files.

## 🎨 API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Generate Video
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! I am Bruce'\''s digital avatar.",
    "language": "en",
    "reference_image": "bruce_neutral.jpg"
  }'
```

### Download Generated Video
```bash
curl http://localhost:8000/api/v1/videos/{filename} -o output.mp4
```

## 🛠️ Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **TTS** | XTTS-v2 | Multilingual voice cloning |
| **Avatar** | LivePortrait | Single-image animation (placeholder) |
| **ASR** | faster-whisper | Phase 3 |
| **LLM** | Qwen-2.5 | Phase 2+ |
| **API** | FastAPI | Python async |
| **Container** | Docker | CPU (local) / GPU (prod) |
| **Orchestration** | Docker Compose | Local dev |
| **Cloud** | GCP Cloud Run GPU | Production |

## 🎯 Performance Targets

- **Resolution**: 256p-360p (latency > quality)
- **FPS**: 25-30
- **Latency** (Phase 3): 450-900ms end-to-end
- **Cost**: < $100/month with scale-to-zero

## 🔧 Configuration

Edit `.env` file (copy from `.env.example`):

```bash
MODE=local          # local or production
DEVICE=cpu          # cpu or cuda
LOG_LEVEL=info
DEFAULT_REFERENCE_IMAGE=bruce_neutral.jpg
```

## 📊 Development Status

### ✅ Completed (Phase 1)
- [x] Project structure and Docker setup
- [x] Runtime service with FastAPI
- [x] XTTS-v2 TTS integration
- [x] Basic avatar animation (placeholder)
- [x] Phase 1 pipeline (script → video)
- [x] Evaluator with test scenarios
- [x] Metrics collection framework
- [x] Voice sample extraction

### 🚧 In Progress
- [ ] LivePortrait full integration
- [ ] Voice quality optimization
- [ ] Model download automation

### 📅 Planned (Phase 2)
- [ ] Qwen LLM integration
- [ ] Semi-interactive chat pipeline
- [ ] React web UI
- [ ] Cloud deployment (Terraform)

### 📅 Planned (Phase 3)
- [ ] faster-whisper ASR
- [ ] Real-time streaming
- [ ] WebRTC integration
- [ ] Production optimization

## 📝 Notes

### Model Downloads
On first run, XTTS-v2 models (~2GB) will be downloaded automatically. This may take several minutes.

### Voice Samples
Voice reference samples are extracted from the video files in `assets/videos/`. Ensure videos contain clear speech in each language (EN/ZH/ES).

### LivePortrait
Current implementation uses a simple video generation as a placeholder. Full LivePortrait integration requires:
- Cloning the LivePortrait repository
- Downloading pre-trained models
- GPU for acceptable performance

## 🤝 Contributing

This is a personal project following the specification in `PROJECT_SPEC.md`.

## 📄 License

Private project - All rights reserved.

---

**Last Updated**: November 6, 2025
**Phase**: 1 (MVP)
**Status**: Development
