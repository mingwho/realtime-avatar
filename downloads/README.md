# Downloads Directory

This directory is for downloading test outputs from GCP instances for local spot checking and comparison.

## Usage

Download outputs from GCP instances:

```bash
# Download a specific output file
gcloud compute scp realtime-avatar-test:/home/$USER/realtime-avatar/runtime/outputs/result.mp4 \
  downloads/gcp_result_$(date +%Y%m%d_%H%M%S).mp4 \
  --zone=us-east1-c

# Or use wildcards to download all outputs
gcloud compute scp realtime-avatar-test:/home/$USER/realtime-avatar/runtime/outputs/*.mp4 \
  downloads/ \
  --zone=us-east1-c
```

## Organization

Suggested naming conventions:
- `gcp_<test-name>_<date>_<gpu-type>.mp4` - For GPU benchmark outputs
- `gcp_gfpgan_<date>.mp4` - For GFPGAN quality tests
- `local_<test-name>_<date>.mp4` - For local M3 comparison outputs

## Spot Checking

After downloading, compare outputs:
1. Visual quality inspection
2. Playback smoothness
3. Lip sync accuracy
4. Face enhancement quality (GFPGAN)
5. File size and encoding quality

## Cleanup

This directory is excluded from git. Clean up periodically:

```bash
# Remove old test files
rm downloads/*_2025*.mp4

# Or clear everything
rm downloads/*.mp4
```
