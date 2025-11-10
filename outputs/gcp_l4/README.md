# GCP L4 GPU Outputs

This directory contains outputs downloaded from the GCP L4 GPU instance for local verification and quality comparison.

## Files

- `tts_test_l4_gpu.wav` - TTS test generated on L4 GPU (16.46s audio, generated in 12.38s = 1.33x realtime)

## Instance Details

- **Instance:** realtime-avatar-test
- **Zone:** us-east1-c
- **GPU:** NVIDIA L4 (23GB VRAM)
- **Cost:** ~$0.60/hour
- **External IP:** 34.139.21.32

## Performance

- **TTS Initialization:** 40.53s (one-time model download)
- **TTS Synthesis:** 12.38s for 16.46s audio
- **Realtime Factor:** 1.33x (faster than realtime)
- **Test Text:** "Hello from the cloud! This is a test of text-to-speech synthesis running on an NVIDIA L4 GPU in Google Cloud Platform. The quick brown fox jumps over the lazy dog."

## Usage

Download outputs from instance:
```bash
gcloud compute scp realtime-avatar-test:/path/to/output outputs/gcp_l4/ --zone=us-east1-c
```

This directory is excluded from git via `.gitignore`.
