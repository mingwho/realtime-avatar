#!/bin/bash
# Install TensorRT 8.6.1 Python bindings in existing container
# Works around apt dependency conflicts by downloading .deb files directly

set -e

echo "Installing TensorRT 8.6.1 Python bindings..."

# Download TensorRT Python wheel for CUDA 12.0
cd /tmp
wget https://developer.download.nvidia.com/compute/machine-learning/tensorrt/secure/8.6.1/tars/TensorRT-8.6.1.6.Linux.x86_64-gnu.cuda-12.0.tar.gz

# Extract
tar -xzf TensorRT-8.6.1.6.Linux.x86_64-gnu.cuda-12.0.tar.gz
cd TensorRT-8.6.1.6

# Install Python wheel
pip install python/tensorrt-8.6.1-cp310-none-linux_x86_64.whl

# Install graphsurgeon and onnx-graphsurgeon
pip install graphsurgeon/graphsurgeon-0.4.6-py2.py3-none-any.whl
pip install onnx_graphsurgeon/onnx_graphsurgeon-0.3.12-py2.py3-none-any.whl

# Verify installation
python -c "import tensorrt as trt; print(f'TensorRT {trt.__version__} installed successfully')"

echo "TensorRT installation complete!"
