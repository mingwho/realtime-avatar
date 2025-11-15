# TensorRT Installation Blockers

## Summary
After 3 attempts across 2 sessions, unable to successfully install TensorRT 8.6.1 Python bindings required for Ditto's official TensorRT engines.

## Context
- **Goal**: Install TensorRT 8.6.1 to use official pre-built TensorRT engines from Ditto team
- **Expected benefit**: 2-3x speedup over current PyTorch baseline (3.07x RTF → potentially <1.5x RTF)
- **TensorRT engines**: Successfully downloaded (2GB, ditto_trt_Ampere_Plus/)
- **Config file**: Downloaded (v0.4_hubert_cfg_trt.pkl)
- **Blocker**: Cannot install Python bindings to load the engines

## Installation Attempts

### Attempt 1: pip install tensorrt-libs + tensorrt (Session 2)
**Approach**: Install in existing ditto-cuda12 container using pip
```bash
pip install tensorrt-libs==8.6.1
pip install tensorrt==8.6.1
```

**Result**: ❌ FAILED

**Error**:
```
subprocess.CalledProcessError: Command '['/usr/bin/python3', '-m', 'pip', 
'install', 'tensorrt_libs==8.6.1', '--index-url', 'https://pypi.nvidia.com'] 
returned non-zero exit status 1.
```

**Root cause**: TensorRT 8.6.1's setup.py has custom build process that expects `/usr/bin/python3 -m pip` to exist. Our container has Python in `/usr/local/bin/`, and pip's shebang points to `/usr/bin/python3` which doesn't exist in the build environment.

**Why this happens**: TensorRT tarball from PyPI uses a custom setup.py that directly invokes system python/pip, not respecting the virtual environment or pip's own Python interpreter.

### Attempt 2: apt install in Docker build (Session 3)
**Approach**: Rebuild Docker image from scratch with TensorRT installed via apt
```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04
RUN apt-get install -y tensorrt=8.6.1.* python3-libnvinfer=8.6.1.*
```

**Result**: ❌ FAILED

**Error**:
```
The following packages have unmet dependencies:
 tensorrt : Depends: libnvinfer-bin (= 8.6.1.6-1+cuda12.0) 
            but 10.14.1.48-1+cuda13.0 is to be installed
```

**Root cause**: NVIDIA's apt repository has been updated and now contains TensorRT 10.x packages (for CUDA 13.0) as the default. The TensorRT 8.6.1 packages (for CUDA 12.0) still exist but their dependencies cannot be satisfied because the repo prefers the newer versions.

**Why this happens**: Package managers resolve to latest available versions. TensorRT 8.6.1 depends on libnvinfer 8.6.1, but apt finds libnvinfer 10.14.1 and tries to use that, creating an impossible dependency tree.

### Attempt 3: Use NVIDIA TensorRT base image (Session 3)
**Approach**: Use pre-built nvidia/tensorrt:23.08-py3 base image
```dockerfile
FROM nvcr.io/nvidia/tensorrt:23.08-py3
```

**Result**: ❌ FAILED

**Error**:
```
ERROR: failed to copy: write /var/lib/docker/buildkit/content/ingest/.../data: 
no space left on device
```

**Root cause**: The NVIDIA TensorRT base image is ~8GB compressed. With existing 17.5GB PyTorch image and limited disk space (50GB disk, 47GB used before cleanup), there wasn't enough room to pull and extract the large base image.

**Why this happens**: TensorRT base images include full CUDA toolkit, TensorRT libs, Python bindings, and samples. Our instance disk is too small for multiple large ML images.

### Attempt 4: Download TensorRT tarball (Session 3)
**Approach**: Download official TensorRT 8.6.1 tarball from NVIDIA and manually install wheels
```bash
wget https://developer.download.nvidia.com/compute/machine-learning/tensorrt/secure/8.6.1/tars/TensorRT-8.6.1.6.Linux.x86_64-gnu.cuda-12.0.tar.gz
```

**Result**: ❌ FAILED

**Error**:
```
HTTP request sent, awaiting response... 302 Moved Temporarily
Location: https://developer.download.nvidia.com/403.html [following]
```

**Root cause**: NVIDIA's TensorRT tarballs are behind authentication/license wall. Requires NVIDIA developer account login even though the direct link is "public".

**Why this happens**: NVIDIA restricts TensorRT downloads to logged-in developers who accept their license terms.

## Technical Analysis

### Why TensorRT 8.6.1 is Hard to Install

1. **Custom build process**: The PyPI package has non-standard setup.py that shells out to system python, not using pip's isolated build environment properly

2. **Repository version skew**: NVIDIA updates their apt repos frequently. TensorRT 8.6.1 dependencies can't be satisfied when newer packages (10.x) are in the same repo

3. **Authentication requirements**: Direct tarball downloads require NVIDIA developer account, can't be scripted

4. **Size constraints**: Pre-built images with TensorRT are 8GB+, too large for our disk space

### Version Compatibility Research

**Available TensorRT versions on PyPI**:
- 8.5.1.7, 8.5.2.2, 8.5.3.1
- 8.6.0, 8.6.1, 8.6.1.post1
- 10.0.1, 10.1.0, 10.2.0, ... 10.14.1.48

**Ditto's TensorRT engines**:
- Built for: TensorRT 8.6.1
- Format: .engine files (12 total, FP16/FP32 mix)
- Target GPU: Ampere+ (L4 is Ampere)

**Compatibility question**: Can TensorRT 10.x load 8.6.1 engines?
- **Backward compatibility**: Generally NO - TensorRT engines are version-specific
- **Forward compatibility**: NO - newer runtime won't load older engines reliably
- **Risk**: Engines would need to be regenerated for TensorRT 10.x

## Alternative Paths Forward

### Option 1: Use Wav2Lip Instead (RECOMMENDED)
**Pros**:
- No TensorRT dependency
- Easier to install and run
- Well-documented in our codebase
- Proven to work in similar projects

**Cons**:
- May be slower than Ditto+TensorRT
- Different visual quality (need to test)

**Implementation**: Already have Wav2Lip pipeline code, just need to test performance

### Option 2: Request Ditto Team for TensorRT 10.x Engines
**Pros**:
- TensorRT 10.x installs cleanly from PyPI
- Would get 2-3x speedup we're looking for
- Official support from Ditto maintainers

**Cons**:
- Requires waiting for team response
- No guarantee they'll provide new engines
- Maintenance burden if they update

**Implementation**: Open GitHub issue on antgroup/ditto-talkinghead

### Option 3: Regenerate TensorRT Engines Ourselves
**Pros**:
- Can use any TensorRT version we want
- Full control over optimization settings
- Can target our specific GPU

**Cons**:
- Requires understanding Ditto's TensorRT conversion code
- Time-consuming process (hours to build all 12 engines)
- Need to verify accuracy matches PyTorch
- Risk of creating broken/slow engines

**Implementation**: Study ditto/tools/export_tensorrt.py (if exists)

### Option 4: Increase Instance Disk and Use TensorRT Base Image
**Pros**:
- Clean solution with pre-tested environment
- TensorRT guaranteed to work
- Can use official 8.6.1 engines

**Cons**:
- Costs more (need 100GB+ disk)
- Still have space management issues long-term
- Doesn't solve Python symlink issues

**Implementation**: Resize disk to 100GB, rebuild with nvidia/tensorrt:23.08-py3

### Option 5: Accept PyTorch and Optimize Elsewhere
**Pros**:
- Already have working baseline (3.07x RTF)
- Can optimize other pipeline components
- No dependency hell

**Cons**:
- Won't hit real-time performance goal (<1.0x RTF)
- Leaves potential 2-3x speedup on table

**Implementation**: Focus on LLM latency, TTS optimization, or switch to lighter model

## Recommendation

Given 3 failed installation attempts and the technical complexity, I recommend **Option 1: Use Wav2Lip** as the path forward.

**Reasoning**:
1. Pragmatic: We need working solution, not perfect solution
2. Time-effective: Can test Wav2Lip performance in <1 hour vs days on TensorRT
3. Risk mitigation: TensorRT installation has proven too brittle
4. Goal-aligned: If Wav2Lip achieves <1.5x RTF, we're close enough to real-time

**Next steps**:
1. Test Wav2Lip with same test video (bruce_haircut_cropped.jpg)
2. Measure RTF and compare to Ditto PyTorch (3.07x)
3. If Wav2Lip is comparable or better, proceed with it
4. If Wav2Lip is significantly worse, revisit TensorRT via Options 2 or 3

## Lessons Learned

1. **Ecosystem fragmentation**: ML tools (TensorRT, ONNX, etc.) have poor cross-version compatibility
2. **Pre-built binary hell**: Python wheels with C++ dependencies are brittle across environments
3. **Documentation gaps**: TensorRT installation docs assume specific system configurations
4. **Trade-offs matter**: Sometimes "good enough" (PyTorch) is better than "perfect but broken" (TensorRT)
5. **Disk space planning**: ML workloads need generous disk space (100GB+ for serious work)

## Time Spent

- Session 2: ~45 minutes (pip install attempts)
- Session 3: ~60 minutes (Docker rebuilds, apt debugging)
- **Total**: ~105 minutes trying to install TensorRT 8.6.1

This is excessive for a single dependency. Cutting losses and trying alternatives is warranted.
