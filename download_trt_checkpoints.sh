#!/bin/bash
# Download TensorRT checkpoints for Ditto (Ampere+ GPUs like L4)

set -e

echo "📥 Downloading TensorRT checkpoints for Ditto..."
echo "Target: checkpoints/ditto_trt_Ampere_Plus/"
echo ""

cd /app/ditto-talkinghead/checkpoints

# Download using huggingface-cli or git lfs
if command -v huggingface-cli &> /dev/null; then
    echo "Using huggingface-cli..."
    huggingface-cli download digital-avatar/ditto-talkinghead \
        --include "ditto_trt_Ampere_Plus/*" \
        --local-dir . \
        --local-dir-use-symlinks False
else
    echo "Installing huggingface-hub..."
    pip install -q huggingface-hub
    
    echo "Downloading TRT checkpoints..."
    python3 << 'PYTHON'
from huggingface_hub import snapshot_download
import os

snapshot_download(
    repo_id="digital-avatar/ditto-talkinghead",
    allow_patterns=["ditto_trt_Ampere_Plus/*", "ditto_cfg/v0.4_hubert_cfg_trt*.pkl"],
    local_dir="/app/ditto-talkinghead/checkpoints",
    local_dir_use_symlinks=False
)
print("✅ TensorRT checkpoints downloaded!")
PYTHON
fi

echo ""
echo "📊 Checkpoint directory sizes:"
du -sh /app/ditto-talkinghead/checkpoints/*

echo ""
echo "✅ Done! Now you can use TRT with:"
echo "   python inference.py --data_root=./checkpoints/ditto_trt_Ampere_Plus --config=v0.4_hubert_cfg_trt.pkl"
