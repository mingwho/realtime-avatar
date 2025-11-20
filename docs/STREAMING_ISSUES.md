# Streaming Implementation - Known Issues & Solutions

## Current Status

✅ **Working:**
- Progressive chunk delivery (chunks arrive one at a time, not batched)
- Sentence splitting with abbreviation handling
- SSE event streaming from backend to frontend
- Video queue with sequential playback
- TTFF improved from ~27s to ~23s

⚠️ **Issue: Video Download Stalls**

### Problem Description

Videos occasionally fail to load with the following symptoms:
- `networkState=2` (NETWORK_LOADING) - browser is trying to download
- `readyState=0` (HAVE_NOTHING) - no data received
- "Video download stalled" event fires
- Timeout after 30s waiting for video data
- **Inconsistent** - sometimes works, sometimes doesn't (especially first chunk)

### Root Cause Analysis

The browser starts downloading the video but doesn't receive data fast enough, causing a stall. This suggests:

1. **Network throughput issue** - video files are large (4-6 seconds of video)
2. **Backend serving bottleneck** - FastAPI FileResponse might not stream efficiently
3. **Cross-origin latency** - localhost → GCP adds overhead
4. **Browser buffering strategy** - Chrome/Safari may aggressively buffer before playing

### Evidence from Logs

```
🎬 Video load started
⚠️ Video download stalled
⏱️ Timeout waiting for video to load after 30s
Current state: readyState=0, networkState=2
Buffered ranges: 0
```

This shows the browser initiates download but receives no bytes.

## Potential Solutions

### Solution 1: Video Preloading Strategy
**Concept:** Start downloading next chunk while current chunk plays

**Implementation:**
```javascript
// In frontend, when chunk N arrives:
1. Add chunk N to queue
2. If chunk N+1 is already known, create hidden <video> element
3. Preload chunk N+1 in background
4. When chunk N finishes, swap to preloaded element

Benefits:
- Masks download time with playback time
- User never waits for download after first chunk
- Browser can use full bandwidth during playback

Tradeoffs:
- More complex state management
- Need to handle preload failures
- Memory overhead (2 video elements)
```

**Estimated complexity:** Medium (2-3 hours)
**Impact:** High - should eliminate most stalls after first chunk

---

### Solution 2: Adaptive Video Quality
**Concept:** Serve lower resolution/bitrate videos for faster delivery

**Implementation:**
```python
# Backend: Generate multiple qualities
- High quality: 512x512, 2Mbps (current)
- Medium quality: 384x384, 1Mbps
- Low quality: 256x256, 512kbps

# Frontend: Detect connection speed
if (navigator.connection.downlink < 2) {
    quality = 'low';
}

# Backend serves appropriate quality
return FileResponse(f"{job_id}_{quality}.mp4")
```

**Estimated complexity:** High (1-2 days for backend changes)
**Impact:** High - smaller files = faster downloads

---

### Solution 3: Video Chunk Compression
**Concept:** Reduce video file size without quality loss

**Implementation:**
```bash
# Current: Ditto generates videos with default settings
# Optimize with ffmpeg post-processing:

ffmpeg -i input.mp4 \
  -c:v libx264 \
  -preset fast \
  -crf 23 \
  -movflags +faststart \
  output.mp4

Flags:
- crf 23: Slightly higher compression
- faststart: Moves moov atom to beginning for streaming
- preset fast: Balance quality vs speed
```

**Estimated complexity:** Low (30 mins)
**Impact:** Medium - 20-30% file size reduction

---

### Solution 4: Range Request Optimization
**Concept:** Enable partial content downloads for better streaming

**Implementation:**
```python
# Backend: Support Range requests properly
from fastapi.responses import FileResponse
import os

@app.get("/api/v1/videos/{filename}")
async def get_video(filename: str, request: Request):
    file_path = os.path.join("/tmp/gpu-service-output", filename)
    
    # Check for Range header
    range_header = request.headers.get("range")
    
    if range_header:
        # Parse range and return partial content
        return StreamingResponse(
            file_iterator(file_path, range_header),
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{size}",
                "Accept-Ranges": "bytes",
            }
        )
    
    return FileResponse(file_path)
```

**Estimated complexity:** Medium (1-2 hours)
**Impact:** Medium - better browser buffering, faster initial playback

---

### Solution 5: CDN/Edge Caching
**Concept:** Cache video chunks closer to user

**Implementation:**
```
Options:
1. GCP Cloud CDN (easy integration)
2. Cloudflare in front of GCP
3. S3 + CloudFront

Trade-off: Adds latency for first user, but helps if videos reused
```

**Estimated complexity:** Medium (depends on infrastructure)
**Impact:** Low for single user, High for multiple users

---

### Solution 6: WebRTC Data Channel
**Concept:** Use WebRTC for faster peer-to-peer video delivery

**Implementation:**
```javascript
// Frontend initiates WebRTC connection
// Backend pushes video chunks over data channel
// Bypasses HTTP overhead

Benefits:
- Lower latency than HTTP
- Better for real-time streaming
- Can prioritize video data

Tradeoffs:
- Complex implementation
- Requires STUN/TURN servers
- More moving parts
```

**Estimated complexity:** Very High (3-5 days)
**Impact:** High - but may be overkill

---

### Solution 7: Fallback to Blob URL
**Concept:** Download entire video as blob, then play

**Implementation:**
```javascript
// Instead of direct video src:
async function loadVideoAsBlob(url) {
    const response = await fetch(url);
    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    videoSource.src = blobUrl;
    avatarVideo.load();
    
    // Cleanup after playback
    avatarVideo.onended = () => {
        URL.revokeObjectURL(blobUrl);
    };
}

Benefits:
- Full control over download
- Can show progress bar
- Retry logic easier

Tradeoffs:
- Must download entire video before playing
- Higher memory usage
```

**Estimated complexity:** Low (1 hour)
**Impact:** Medium - trades download time for reliability

---

## Recommended Approach

**Phase 1 (Quick wins):**
1. **Video compression** (Solution 3) - 30 mins, immediate impact
2. **Blob URL fallback** (Solution 7) - 1 hour, improves reliability

**Phase 2 (Core fix):**
3. **Preloading strategy** (Solution 1) - 3 hours, best UX improvement

**Phase 3 (Optional optimization):**
4. **Adaptive quality** (Solution 2) - if users have slow connections
5. **Range requests** (Solution 4) - if compression isn't enough

## Testing Strategy

For each solution, measure:
- **TTFF** (time to first frame) - should be < 20s
- **Stall rate** - % of chunks that timeout
- **Total playback time** - all chunks should play smoothly
- **Network transfer** - MB downloaded per conversation

Target metrics:
- TTFF: < 15s (currently ~23s)
- Stall rate: < 5% (currently ~30-50%)
- Smooth playback: no gaps between chunks

## Next Session Plan

1. Implement video compression (faststart flag is critical)
2. Add blob URL fallback with progress tracking
3. Test stall rate improvement
4. If still issues, implement preloading strategy
