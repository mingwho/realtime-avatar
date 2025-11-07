# Gold Standard Test Set

## Purpose
This directory contains real video clips of Bruce speaking specific phrases. These serve as "ground truth" references to validate the quality of synthetically generated videos.

## Usage

**Key Principle:** Gold set is for **validation only**, not training.
- ✅ Use to measure quality degradation (real → synthetic)
- ✅ Use for regression testing (is quality improving?)
- ✅ Use alongside novel phrase testing
- ❌ Don't use these phrases in training data
- ❌ Don't optimize hyperparameters solely for gold set scores

## Directory Structure

```
gold_standard/
├── clips/              # Short video clips extracted from originals
│   ├── en_001.mp4     # "Hello, my name is Bruce"
│   ├── en_002.mp4     # Medium length phrase
│   ├── zh_001.mp4     # Chinese phrase
│   └── ...
├── phrases.json       # Metadata: text, language, timestamps, difficulty
└── README.md         # This file
```

## Gold Set Phrases

Designed to test:
- **Variety in length:** Short (2-5 words), Medium (6-15 words), Long (16+ words)
- **Languages:** English, Chinese (Mandarin), Spanish
- **Difficulty:** Easy (common words), Medium (natural speech), Hard (complex/technical)
- **Use cases:** Greetings, professional context, casual conversation

## Current Status

**Source Videos:**
- `bruce_english.mp4` - 185s English speech
- `bruce_mandarin.mp4` - 65s Mandarin speech  
- `bruce_spanish.mp4` - 65s Spanish speech
- `bruce_expressive_motion.mp4` - 68s with more facial expressions

**Action Required:**
You need to identify specific phrases from these videos and their timestamps.
See `phrases_template.json` for the format.

## Next Steps

1. **Watch your source videos** and identify 5-10 clear phrases
2. **Note timestamps** where each phrase occurs
3. **Update `phrases.json`** with the text and timestamps
4. **Run extraction script** to create clips from timestamps
5. **Add gold set tests** to evaluator scenarios

## Avoiding Overfitting

- Gold set phrases should be **different** from voice reference samples
- Test on **both** gold set (known) and novel phrases (unknown)
- Keep gold set small (5-10 phrases) for MVP
- Expand later with more variety
