## Preconditions
- gcloud installed and authenticated; project set to the one hosting `realtime-avatar-test`
- Instance name: `realtime-avatar-test`; zone: `us-east1-c`
- Run commands from repo root: `/Users/brucegarro/project/realtime-avatar`

## Start Instance
- Start compute instance:
  - `gcloud compute instances start realtime-avatar-test --zone=us-east1-c`
- Fetch public IP for backend:
  - `GCP_IP=$(gcloud compute instances describe realtime-avatar-test --zone=us-east1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP)')`
  - `echo $GCP_IP`

## Verify Backend Services
- Health checks from local:
  - `curl http://$GCP_IP:8000/health`
  - `curl http://$GCP_IP:8001/health`
- If not healthy, SSH and start containers on the instance:
  - `gcloud compute ssh realtime-avatar-test --zone=us-east1-c --command='cd ~/realtime-avatar && docker compose up -d runtime gpu-service'`
  - Optional: verify with `docker compose ps` and `nvidia-smi`

## Configure Local Web UI
- Point web UI to the backend IP:
  - `cd web`
  - `./configure_web.sh $GCP_IP`
- Start local web container:
  - `docker compose up -d`
- Access the app:
  - `open http://localhost:8080`

## End-to-End Validation
- Backend health: `curl http://$GCP_IP:8000/health && curl http://$GCP_IP:8001/health`
- API test (optional):
  - `curl -X POST http://$GCP_IP:8000/api/v1/conversation -F "audio=@sample.wav" --output avatar_response.mp4`

## Notes & Pitfalls
- IP changes after start: re-run `./configure_web.sh $GCP_IP`
- Firewall must allow `tcp:8000,tcp:8001`; add rule if health checks fail
- If containers crash on boot, run `docker compose logs -f` on the instance for diagnostics

## Stop & Cleanup
- Stop instance when done:
  - `gcloud compute instances stop realtime-avatar-test --zone=us-east1-c`
- Stop local web:
  - `cd web && docker compose down`

Confirm and I will execute these steps now.