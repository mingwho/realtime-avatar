#!/bin/bash
# Configure Web UI for Hybrid Deployment
# Usage: ./configure_web.sh [GCP_INSTANCE_IP]

set -e

if [ -z "$1" ]; then
    echo "Usage: ./configure_web.sh <GCP_INSTANCE_IP>"
    echo ""
    echo "Example:"
    echo "  ./configure_web.sh 34.73.123.45"
    echo ""
    echo "Or get IP automatically:"
    echo "  ./configure_web.sh \$(gcloud compute instances describe realtime-avatar --zone=us-east1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
    exit 1
fi

GCP_IP="$1"
APP_JS="app.js"

echo "================================================"
echo "Configuring Web UI for Hybrid Deployment"
echo "================================================"
echo ""
echo "Backend API: http://$GCP_IP:8000"
echo ""

# Check if app.js exists
if [ ! -f "$APP_JS" ]; then
    echo "❌ Error: $APP_JS not found"
    echo "Run this script from the web/ directory"
    exit 1
fi

# Backup original
if [ ! -f "$APP_JS.backup" ]; then
    cp "$APP_JS" "$APP_JS.backup"
    echo "✓ Created backup: $APP_JS.backup"
fi

# Update API_BASE_URL in app.js
sed -i.tmp "s|const API_BASE_URL = 'http://localhost:8000';|const API_BASE_URL = 'http://$GCP_IP:8000';|g" "$APP_JS"
rm -f "$APP_JS.tmp"

echo "✓ Updated API endpoint in $APP_JS"
echo ""

# Verify the change
echo "Current configuration:"
grep "API_BASE_URL" "$APP_JS" | head -1
echo ""

echo "================================================"
echo "✅ Configuration Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Build and run web container:"
echo "   docker compose up -d --build"
echo ""
echo "2. Access web UI:"
echo "   http://localhost:8080"
echo ""
echo "3. To revert to localhost backend:"
echo "   cp $APP_JS.backup $APP_JS"
echo ""
