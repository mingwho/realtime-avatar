#!/bin/bash
# Phase 4 Complete Deployment - One-Command Setup
# Usage: ./deploy_phase4_hybrid.sh

set -e

PROJECT_ROOT="/Users/brucegarro/project/realtime-avatar"
GCP_ZONE="us-east1-c"
INSTANCE_NAME="realtime-avatar-test"

echo "========================================================"
echo "Phase 4 Hybrid Deployment - Complete Setup"
echo "========================================================"
echo ""

cd "$PROJECT_ROOT"

# Step 1: Deploy Backend
echo "📦 Step 1: Deploying backend to GCP L4 GPU..."
echo ""
cd scripts/
./deploy_gcp_backend.sh

echo ""
echo "✅ Backend deployed"
echo ""

# Step 2: Get GCP IP
echo "📡 Step 2: Getting GCP instance IP..."
GCP_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
  --zone="$GCP_ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "✅ Backend IP: $GCP_IP"
echo ""

# Step 3: Configure Web UI
echo "⚙️  Step 3: Configuring web UI..."
cd "$PROJECT_ROOT/web/"
./configure_web.sh "$GCP_IP"

echo ""

# Step 4: Build and Start Web Container
echo "🐳 Step 4: Building and starting web container..."
docker compose up -d --build

echo ""

# Wait for container to be ready
echo "⏳ Waiting for web container to be ready..."
sleep 5

# Verify everything is running
echo ""
echo "🔍 Verifying deployment..."
echo ""

# Check web container
if docker compose ps | grep -q "Up"; then
    echo "✅ Web container: Running"
else
    echo "❌ Web container: Failed"
    exit 1
fi

# Check backend health
if curl -f -s "http://$GCP_IP:8000/health" > /dev/null; then
    echo "✅ Backend health: OK"
else
    echo "⚠️  Backend health: Not responding (may still be initializing)"
fi

echo ""
echo "========================================================"
echo "✅ Phase 4 Deployment Complete!"
echo "========================================================"
echo ""
echo "🌐 Web UI: http://localhost:8080"
echo "🔌 Backend API: http://$GCP_IP:8000"
echo ""
echo "📋 Quick Actions:"
echo ""
echo "  Open Web UI:"
echo "    open http://localhost:8080"
echo ""
echo "  View Web Logs:"
echo "    docker compose logs -f web"
echo ""
echo "  View Backend Logs:"
echo "    gcloud compute ssh $INSTANCE_NAME --zone=$GCP_ZONE --command='docker compose logs -f runtime'"
echo ""
echo "  Test Backend Health:"
echo "    curl http://$GCP_IP:8000/health"
echo ""
echo "  Stop Web Container:"
echo "    docker compose down"
echo ""
echo "  Stop GCP Instance (save costs):"
echo "    gcloud compute instances stop $INSTANCE_NAME --zone=$GCP_ZONE"
echo ""
echo "📖 Full Guide: PHASE4_DEPLOYMENT.md"
echo ""
