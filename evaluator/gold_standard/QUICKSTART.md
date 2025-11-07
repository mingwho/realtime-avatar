# Quick Start: Gold Standard Setup

## Do I Need to Record New Audio?

**No! You can use your existing videos.** You already have:
- ✅ `bruce_english.mp4` (3 min)
- ✅ `bruce_mandarin.mp4` (1 min)
- ✅ `bruce_spanish.mp4` (1 min)  
- ✅ `bruce_expressive_motion.mp4` (1 min)

These are perfect for creating a gold set!

## Setup Steps (5-10 minutes)

### 1. Watch Your Videos & Note Phrases

```bash
# Helper script to get started
python create_phrases.py
```

Or watch manually and note:
- What you said (exact text)
- When you said it (start & end timestamps)

**Goal:** Identify 5-10 clear phrases total across all languages.

### 2. Create phrases.json

Copy the template:
```bash
cp phrases_template.json phrases.json
```

Edit `phrases.json` and replace:
- `REPLACE_WITH_ACTUAL_TEXT` → actual text you spoke
- `start_time` and `end_time` → actual timestamps from videos
- Add more phrases as needed

### 3. Extract Video Clips

```bash
python extract_clips.py
```

This creates short clips in `clips/` directory.

### 4. Verify Clips

Check that clips show the right phrases:
```bash
ls -lh clips/
# Play a clip to verify
open clips/en_001.mp4
```

### 5. Run Gold Set Tests

```bash
# From evaluator directory
cd ..
docker compose --profile evaluator up evaluator
```

The evaluator will now include gold set comparisons!

## Example phrases.json Entry

```json
{
  "id": "en_001",
  "text": "Hello, my name is Bruce",
  "language": "en",
  "source_video": "bruce_english.mp4",
  "start_time": 10.5,
  "end_time": 13.2,
  "duration": 2.7,
  "difficulty": "easy",
  "use_case": "greeting",
  "notes": "Clear introduction",
  "clip_path": "clips/en_001.mp4"
}
```

## Recommended Phrase Mix

For MVP, aim for **5-10 phrases total**:

- **3-4 English phrases:**
  - 1 short (2-5 sec): greeting/intro
  - 1 medium (5-10 sec): professional statement
  - 1 longer (10-15 sec): explanation/story
  - 1 with emotion/expression

- **2-3 Chinese phrases:**
  - 1 short greeting
  - 1 medium sentence

- **1-2 Spanish phrases:**
  - 1 short greeting
  - 1 medium sentence

## Tips

- **Use VLC or QuickTime** to find timestamps
  - VLC shows time in bottom toolbar
  - QuickTime: hover over progress bar
  
- **Be precise with timestamps**
  - Start clip slightly before speech begins
  - End slightly after speech ends
  - Aim for natural boundaries (breaths, pauses)

- **Variety matters**
  - Mix short and long phrases
  - Include different speaking styles
  - Test both clear and challenging audio

## What Gets Tested

When you run the evaluator with gold set tests, it will:

1. Generate synthetic video for each phrase
2. Compare to your real video clip
3. Report metrics:
   - Duration matching ✅ (already working)
   - Visual similarity 🚧 (future)
   - Audio similarity 🚧 (future)
   - Lip sync quality 🚧 (future)

For Phase 1 MVP, we're just validating the pipeline works.
Advanced comparison metrics come in Phase 2.

## Need Help?

Run the interactive helper:
```bash
python create_phrases.py
```

It will guide you through the process!
