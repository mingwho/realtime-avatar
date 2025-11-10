#!/bin/bash
# Setup script for LivePortrait
# Downloads LivePortrait repository and model weights

set -e

echo "=== LivePortrait Setup ==="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RUNTIME_DIR="$SCRIPT_DIR/runtime"
LIVEPORTRAIT_DIR="$RUNTIME_DIR/LivePortrait"

cd "$RUNTIME_DIR"

# Clone LivePortrait if not exists
if [ ! -d "$LIVEPORTRAIT_DIR" ]; then
    echo "📥 Cloning LivePortrait repository..."
    git clone https://github.com/KwaiVGI/LivePortrait.git
    echo "✅ LivePortrait cloned"
else
    echo "✅ LivePortrait already exists"
fi

cd "$LIVEPORTRAIT_DIR"

# Install requirements
echo "📦 Installing LivePortrait dependencies..."
pip install -r requirements.txt

# Download model weights
echo "📥 Downloading LivePortrait model weights..."
if [ -f "scripts/download_models.py" ]; then
    python scripts/download_models.py
elif [ -f "scripts/download_models.sh" ]; then
    bash scripts/download_models.sh
else
    echo "⚠️  Model download script not found. Models will download at runtime."
fi

echo ""
echo "✅ LivePortrait setup complete!"
echo ""
echo "Usage:"
echo "  Local (MPS):  AVATAR_BACKEND=sadtalker docker-compose up"
echo "  Cloud (CUDA): AVATAR_BACKEND=liveportrait docker-compose up"
echo ""
