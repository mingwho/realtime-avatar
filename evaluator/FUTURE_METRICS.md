# Future Metrics Ideas

## Overview
This document captures advanced metric ideas for future phases beyond the MVP.
These are valuable improvements but not critical for Phase 1 validation.

## Critical Gaps Identified

### 1. Motion Detection (High Priority)
**Problem:** Current lip sync metric scored 1.0 on a completely static video.

**Solution:** Frame-to-frame variance analysis
```python
def calculate_motion_score(video_path: str) -> Dict[str, float]:
    """
    Analyze frame-to-frame differences to detect motion.
    Returns:
        - variance: Overall pixel variance between frames
        - motion_frames_pct: % of frames with significant motion
        - is_static: Boolean if video appears static
    """
```

**Dependencies:** OpenCV only (already installed)

---

### 2. Facial Landmarks Tracking (High Priority)
**Problem:** No validation that mouth actually moves during speech.

**Solution:** MediaPipe face mesh for mouth landmark tracking
```python
def analyze_mouth_movement(video_path: str, audio_path: str) -> Dict[str, float]:
    """
    Track mouth landmarks and correlate with audio amplitude.
    Returns:
        - mouth_movement_score: How much mouth moves (0-1)
        - audio_visual_correlation: Correlation between audio peaks and mouth movement
        - landmark_confidence: Average confidence of face detection
    """
```

**Dependencies:** `mediapipe` (new dependency)

---

### 3. Voice Similarity Scoring (Medium Priority)
**Problem:** No validation that generated voice matches Bruce's reference voice.

**Solution:** Speaker embeddings comparison using resemblyzer
```python
def calculate_voice_similarity(
    generated_audio: str,
    reference_audio: str
) -> Dict[str, float]:
    """
    Compare generated voice to reference using speaker embeddings.
    Returns:
        - similarity_score: Cosine similarity (0-1)
        - is_same_speaker: Boolean threshold check
    """
```

**Dependencies:** `resemblyzer` or `speechbrain` (new dependency)

---

## Additional Quality Metrics (Lower Priority)

### Visual Quality
- **Face detection confidence** - Is there actually a face?
- **Head pose consistency** - Natural movement vs. jitter
- **Eye gaze realism** - Are eyes frozen or moving?
- **Lighting consistency** - Across frames
- **Artifact detection** - Blurring, distortion, uncanny valley effects

### Audio Quality
- **Prosody analysis** - Natural speech rhythm, intonation
- **Pronunciation quality** - Especially for multilingual
- **Emotional consistency** - Does tone match intent?
- **Background noise level** - Clean audio output
- **Clipping detection** - Audio not distorted

### Sync Quality
- **Audio-visual correlation** - Motion correlates with speech amplitude
- **Temporal coherence** - Smooth transitions between frames
- **Phoneme-to-viseme mapping** - Specific sounds match mouth shapes

---

## Recommended Metric Weights (Future)

```python
METRIC_WEIGHTS = {
    "audio_quality": 0.15,
    "video_quality": 0.10,
    "motion_detection": 0.20,  # NEW - High weight
    "facial_landmarks": 0.25,  # NEW - Highest weight
    "voice_similarity": 0.15,  # NEW
    "lip_sync": 0.10,          # Reduced from implicit high weight
    "latency": 0.05,
}

QUALITY_THRESHOLDS = {
    "motion": {
        "is_static": False,  # Must not be static
        "motion_frames_pct": 0.8,  # 80% of frames should have motion
    },
    "voice": {
        "similarity": 0.75,  # Must match reference voice
    },
    "lip_sync": {
        "mouth_movement_avg": 0.001,  # Must have mouth movement
        "has_mouth_movement": True,
    }
}
```

---

## Implementation Priority

### Phase 1 (Critical - catches static video bug)
1. ✅ Motion detection - Quick win, catches static videos
2. ✅ Facial landmarks tracking - Real lip sync quality

### Phase 2 (Quality improvements)
3. Voice similarity - Ensures voice cloning works
4. Face detection confidence - Basic sanity check
5. Artifact detection - Quality issues

### Phase 3 (Polish)
6. Prosody analysis - Natural speech rhythm
7. Emotional consistency - Tone matching
8. Eye gaze tracking - Realism

---

## Dependencies to Add

```txt
# For facial landmarks
mediapipe>=0.10.0

# For voice similarity
resemblyzer>=0.1.1
# OR
speechbrain>=0.5.0

# For advanced audio analysis
praat-parselmouth>=0.4.0  # Prosody
pyworld>=0.3.0  # Pitch analysis
```

---

## References

- MediaPipe Face Mesh: https://google.github.io/mediapipe/solutions/face_mesh
- Resemblyzer for speaker verification: https://github.com/resemble-ai/Resemblyzer
- Lip sync research: Audio-visual speech synchronization metrics
- Motion detection: Frame differencing and optical flow methods
