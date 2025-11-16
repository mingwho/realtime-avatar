# Setup & Deployment Guide

Complete guide for setting up and deploying the Realtime Avatar system locally and on GCP.

## Table of Contents

- [Quick Start (Local M3 Mac)](#quick-start-local-m3-mac)
- [GCP Deployment (L4 GPU)](#gcp-deployment-l4-gpu)
- [Configuration](#configuration)
- [API Testing](#api-testing)
- [Troubleshooting](#troubleshooting)

---

## Quick Start (Local M3 Mac)

### Prerequisites

- macOS with Apple Silicon (M3 or better recommended)
- Docker Desktop with 8GB+ memory
- Python 3.10+
- 30GB disk space
- FFmpeg (for video processing)

### 1. Environment Check

```bash
python3 scripts/check_environment.py
```

This verifies Docker, FFmpeg, and project structure.

### 2. Extract Voice Samples

```bash
./scripts/extract_voice_samples.sh
```

Creates WAV files in `assets/voice/reference_samples/` for voice cloning.

### 3. Setup GPU Service (MPS Acceleration)

The GPU service runs **natively on macOS** for MPS acceleration (5-10x faster than CPU):

```bash
cd runtime
./setup_gpu_service.sh  # Creates venv, installs dependencies
```

### 4. Start GPU Service

In **Terminal 1**:

```bash
cd runtime
./run_gpu_service.sh
```

Service starts on `http://localhost:8001`. You should see:

```
✅ MPS device detected - GPU acceleration enabled!
INFO: Uvicorn running on http://0.0.0.0:8001
```

### 5. Start Runtime Service

In **Terminal 2**:

```bash
docker compose up runtime
```

**First run takes 10-15 minutes** to download XTTS-v2 models (~2GB). Watch for:

```
INFO - XTTS-v2 model loaded in X.XXs
INFO - Phase 1 pipeline ready in X.XXs
```

### 6. Test the System

In **Terminal 3**:

```bash
# Check GPU service health
curl http://localhost:8001/health

# Check runtime health
curl http://localhost:8000/health

# Generate your first video
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! I am Bruce'\''s digital avatar.",
    "language": "en"
  }'
```

### 7. Run Evaluator (Optional)

In **Terminal 3**:

```bash
docker compose --profile evaluator up evaluator
```

Results saved to `evaluator/outputs/`.

### Expected Performance (Local M3)

| Component | Time | Notes |
|-----------|------|-------|
| TTS (XTTS-v2) | 0.54x RTF | Faster than realtime with MPS! |
| Avatar (Ditto) | ~40-50s | For 10s video (CPU) |
| Total | ~1-2 min | For short videos |

---

## GCP Deployment (L4 GPU)

### Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed and authenticated
- L4 GPU quota (request if needed)

### 1. Create GCP Instance

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Create firewall rule (one-time)
gcloud compute firewall-rules create allow-http-8000-8001 \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:8000,tcp:8001 \
  --source-ranges=0.0.0.0/0

# Create L4 GPU instance
gcloud compute instances create realtime-avatar \
  --zone=us-east1-c \
  --machine-type=g2-standard-4 \
  --accelerator=type=nvidia-l4,count=1 \
  --maintenance-policy=TERMINATE \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=200GB \
  --boot-disk-type=pd-balanced
```

**Cost:** ~$0.60/hour for L4 GPU

### 2. Install NVIDIA Drivers

SSH into instance:

```bash
gcloud compute ssh realtime-avatar --zone=us-east1-c
```

Install drivers (takes 5-10 minutes):

```bash
# Install NVIDIA driver
curl https://raw.githubusercontent.com/GoogleCloudPlatform/compute-gpu-installation/main/linux/install_gpu_driver.py --output install_gpu_driver.py
sudo python3 install_gpu_driver.py

# Verify installation
nvidia-smi  # Should show L4 GPU with 24GB VRAM
```

### 3. Install Docker & NVIDIA Container Toolkit

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 4. Deploy the Application

```bash
# Clone repository
git clone https://github.com/brucegarro/realtime-avatar.git
cd realtime-avatar

# Copy assets (or mount from GCS)
# ... upload your reference images and voice samples ...

# Build Docker images
./scripts/build_images.sh

# Start services
docker compose up -d runtime
```

### 5. Test Remote Deployment

From your local machine:

```bash
# Get instance IP
INSTANCE_IP=$(gcloud compute instances describe realtime-avatar \
  --zone=us-east1-c \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Test health
curl http://$INSTANCE_IP:8000/health

# Generate video
curl -X POST http://$INSTANCE_IP:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the cloud!", "language": "en"}'
```

### Expected Performance (L4 GPU with TensorRT)

| Component | RTF | Throughput |
|-----------|-----|------------|
| TTS (XTTS-v2) | **0.70x** | Faster than realtime |
| Ditto TensorRT | **1.23x** | Near realtime (20.3 FPS) |
| Combined | **1.95x** | Full pipeline |
| Concurrent (2 workers) | N/A | **3,685 videos/hour** |

### 6. Stop/Delete Instance

```bash
# Stop (saves disk, stops billing for compute)
gcloud compute instances stop realtime-avatar --zone=us-east1-c

# Start again later
gcloud compute instances start realtime-avatar --zone=us-east1-c

# Delete (removes everything)
gcloud compute instances delete realtime-avatar --zone=us-east1-c
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# GPU Service
GPU_SERVICE_URL=http://localhost:8001  # or remote IP
USE_GPU_SERVICE=true

# Model Configuration
MODEL_CACHE_DIR=/models
TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2

# Avatar Backend
AVATAR_BACKEND=ditto  # ditto, sadtalker, or liveportrait

# Concurrent Workers (GCP only)
CONCURRENT_WORKERS=2  # 1-3 workers for L4 GPU
```

### Docker Compose Configuration

**Local Development (with GPU service):**

```yaml
# docker-compose.yml
services:
  runtime:
    environment:
      - GPU_SERVICE_URL=http://host.docker.internal:8001
      - USE_GPU_SERVICE=true
```

**GCP Deployment (standalone):**

```yaml
services:
  runtime:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Concurrent Workers Configuration

For high-throughput on GCP L4:

```python
# runtime/config.py
CONCURRENT_WORKERS = 2  # Recommended for 24GB VRAM
```

**Memory Usage:**

| Workers | VRAM Usage | Throughput |
|---------|------------|------------|
| 1 worker | 6.7GB (28%) | 1,940 videos/hour |
| 2 workers | 9.5GB (41%) | 3,685 videos/hour ✅ |
| 3 workers | 12.4GB (54%) | 5,044 videos/hour |

---

## API Testing

### Health Checks

```bash
# GPU Service
curl http://localhost:8001/health

# Runtime Service
curl http://localhost:8000/health
```

### Generate Videos

**English:**

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! This is a test.",
    "language": "en",
    "reference_image": "bruce_neutral.jpg"
  }'
```

**Chinese:**

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好！这是一个测试。",
    "language": "zh-cn"
  }'
```

**Spanish:**

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¡Hola! Esto es una prueba.",
    "language": "es"
  }'
```

### List Assets

```bash
# List images
curl http://localhost:8000/api/v1/assets/images

# List voice samples
curl http://localhost:8000/api/v1/assets/voice-samples
```

### Download Generated Video

```bash
# Get video URL from generation response
curl http://localhost:8000/api/v1/videos/FILENAME.mp4 -o output.mp4
```

---

## Troubleshooting

### Models Not Downloading

**Problem:** XTTS-v2 models fail to download

**Solution:**

```bash
# Check internet connection
# Increase timeout in config
# Manually download inside container:
docker compose exec runtime python -c "
from TTS.api import TTS
tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2')
"
```

### GPU Not Detected

**macOS (MPS):**

```bash
# Check MPS availability
python3 -c "import torch; print(torch.backends.mps.is_available())"

# Should return: True
```

**GCP (CUDA):**

```bash
# Check NVIDIA driver
nvidia-smi

# Check PyTorch CUDA
python3 -c "import torch; print(torch.cuda.is_available())"

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Out of Memory

**Docker:**

```bash
# Increase Docker memory: Docker Desktop → Resources → Memory → 8GB+
```

**GCP:**

```bash
# Reduce concurrent workers
export CONCURRENT_WORKERS=1

# Or upgrade to larger instance
# g2-standard-8 (32GB VRAM, 2x L4)
```

### Slow Generation

**Expected times:**

- **CPU mode:** 30-60s for short videos (normal)
- **M3 MPS:** 10-20s for short videos
- **L4 GPU:** 5-10s for short videos
- **L4 TensorRT:** 2-5s for short videos

**Improvements:**

```bash
# Enable GPU service (local)
USE_GPU_SERVICE=true

# Enable TensorRT (GCP)
AVATAR_BACKEND=ditto-trt

# Reduce diffusion steps (quality vs speed)
DITTO_DIFFUSION_STEPS=25  # Default: 50
```

### Connection Refused (GPU Service)

**Problem:** Runtime can't connect to GPU service

**Solution:**

```bash
# Check GPU service is running
curl http://localhost:8001/health

# Check firewall (GCP)
gcloud compute firewall-rules list | grep 8001

# Update GPU_SERVICE_URL in .env
# For Docker on Mac: http://host.docker.internal:8001
# For GCP: http://INTERNAL_IP:8001
```

### TensorRT Not Working

**Problem:** TensorRT fails to load or crashes

**Solution:**

```bash
# Check CUDA version
nvidia-smi  # Should show CUDA 12.x

# Check TensorRT installation
python3 -c "import tensorrt; print(tensorrt.__version__)"

# Fallback to PyTorch
AVATAR_BACKEND=ditto  # instead of ditto-trt
```

### Port Already in Use

**Problem:** Port 8000 or 8001 already in use

**Solution:**

```bash
# Check what's using the port
lsof -i :8000
lsof -i :8001

# Kill the process or change port in docker-compose.yml
# Change "8000:8000" to "8002:8000"
```

---

## Development Workflow

### Normal Development Cycle

```bash
# Terminal 1: GPU Service (if using MPS)
cd runtime && ./run_gpu_service.sh

# Terminal 2: Runtime (auto-reload enabled)
docker compose up runtime

# Terminal 3: Test changes
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Test", "language": "en"}'
```

### View Logs

```bash
# Runtime logs
docker compose logs -f runtime

# Evaluator logs
docker compose logs -f evaluator

# GPU service logs (if running as service)
tail -f runtime/gpu_service.log
```

### Clean Rebuild

```bash
# Stop everything
docker compose down -v

# Rebuild images
./scripts/build_images.sh

# Start fresh
docker compose up runtime
```

---

## Next Steps

- See [PERFORMANCE.md](PERFORMANCE.md) for benchmarks and optimization tips
- See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current development status
- See [README.md](README.md) for project overview
