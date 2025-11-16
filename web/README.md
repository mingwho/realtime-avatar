# Web Interface - Phase 4 ✅

Interactive voice conversation web app with push-to-talk functionality.

## Features

- 🎙️ **Push-to-talk voice input** (Google-style microphone button)
- 🤖 **Real-time avatar responses** (voice cloned video generation)
- 💬 **Live conversation transcript** (user + assistant messages)
- 🌍 **Multi-language support** (English, Chinese, Spanish)
- 📱 **Responsive design** (desktop + mobile)
- 💾 **Optional conversation history** (browser localStorage)

## Quick Start

### 1. Deploy Backend to GCP L4 GPU

```bash
cd scripts/
./deploy_gcp_backend.sh
```

### 2. Configure Web UI

```bash
cd web/
GCP_IP=$(gcloud compute instances describe realtime-avatar --zone=us-east1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
./configure_web.sh $GCP_IP
```

### 3. Run Web Container

```bash
docker compose up -d --build
```

### 4. Access App

**http://localhost:8080**

## Usage

1. Hold microphone button to record
2. Release to send
3. Wait ~35s for avatar response
4. Watch video automatically

## Docker Commands

```bash
docker compose up -d --build  # Build and start
docker compose logs -f        # View logs
docker compose down           # Stop
docker compose restart web    # Restart
```

## Performance (L4 GPU)

- ASR: 1-2s
- LLM: 3-5s  
- Video: 1.23x RTF (TensorRT)
- **Total: ~35s for 17s audio**

## Troubleshooting

```bash
# Check backend health
curl http://YOUR_IP:8000/health

# View logs
docker compose logs -f web

# Check GCP instance
gcloud compute ssh realtime-avatar --zone=us-east1-c --command='docker compose ps'
```

## Files

- `index.html` - UI structure
- `app.js` - Voice recording + API calls
- `styles.css` - Responsive styling
- `Dockerfile` - Nginx container
- `docker-compose.yml` - Container orchestration
- `configure_web.sh` - Backend configuration helper
