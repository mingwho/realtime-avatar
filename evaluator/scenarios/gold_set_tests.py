"""
Gold Set Tests - Compare synthetic generation to real video clips

These tests validate avatar quality by comparing synthetically generated
videos to real recordings of Bruce speaking the same phrases.

Metrics compared:
- Visual similarity (frame comparison)
- Audio similarity (voice matching)
- Duration matching
- Overall quality degradation (real → synthetic)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List
import requests

logger = logging.getLogger(__name__)

# Load gold standard configuration
GOLD_STANDARD_DIR = Path(__file__).parent.parent / 'gold_standard'
PHRASES_FILE = GOLD_STANDARD_DIR / 'phrases.json'


def load_gold_phrases() -> List[Dict]:
    """Load gold standard phrases from configuration"""
    if not PHRASES_FILE.exists():
        logger.warning("Gold standard phrases.json not found - skipping gold set tests")
        return []
    
    with open(PHRASES_FILE, 'r') as f:
        config = json.load(f)
    
    # Filter out placeholder phrases
    valid_phrases = [
        p for p in config['phrases']
        if p['text'] != 'REPLACE_WITH_ACTUAL_TEXT'
    ]
    
    return valid_phrases


def test_gold_set_generation(runtime_url: str) -> Dict:
    """
    Generate synthetic videos for all gold set phrases.
    
    Returns metrics comparing synthetic to real videos.
    """
    phrases = load_gold_phrases()
    
    if not phrases:
        return {
            'status': 'skipped',
            'reason': 'No gold standard phrases configured',
            'results': []
        }
    
    logger.info(f"Running gold set tests for {len(phrases)} phrases")
    
    results = []
    
    for phrase in phrases:
        logger.info(f"Testing phrase: {phrase['id']} - {phrase['text'][:50]}...")
        
        try:
            # Generate synthetic video
            response = requests.post(
                f"{runtime_url}/api/v1/generate",
                json={
                    'text': phrase['text'],
                    'language': phrase['language']
                },
                timeout=300
            )
            response.raise_for_status()
            gen_result = response.json()
            
            # Get real video path
            real_clip_path = GOLD_STANDARD_DIR / phrase['clip_path']
            
            if not real_clip_path.exists():
                logger.warning(f"Real clip not found: {real_clip_path}")
                results.append({
                    'phrase_id': phrase['id'],
                    'status': 'error',
                    'error': 'Real clip not extracted yet'
                })
                continue
            
            # Compare synthetic to real
            # TODO: Implement comparison metrics
            # For MVP, just record that both exist
            
            result = {
                'phrase_id': phrase['id'],
                'text': phrase['text'],
                'language': phrase['language'],
                'difficulty': phrase['difficulty'],
                'status': 'completed',
                'synthetic_duration_ms': gen_result['metadata']['duration_ms'],
                'real_duration_s': phrase['duration'],
                'real_clip': str(real_clip_path),
                'synthetic_url': gen_result.get('video_url', ''),
                # Comparison metrics (placeholder for now)
                'metrics': {
                    'visual_similarity': None,  # TODO: Implement SSIM/PSNR
                    'audio_similarity': None,   # TODO: Implement speaker comparison
                    'duration_match': abs(
                        gen_result['metadata']['duration_ms'] / 1000 - phrase['duration']
                    ) < 0.5,  # Within 0.5s
                }
            }
            
            results.append(result)
            logger.info(f"  ✓ {phrase['id']} completed")
            
        except Exception as e:
            logger.error(f"  ✗ {phrase['id']} failed: {e}")
            results.append({
                'phrase_id': phrase['id'],
                'status': 'error',
                'error': str(e)
            })
    
    # Calculate summary statistics
    completed = [r for r in results if r['status'] == 'completed']
    duration_matches = sum(
        1 for r in completed 
        if r.get('metrics', {}).get('duration_match', False)
    )
    
    return {
        'status': 'completed',
        'total_phrases': len(phrases),
        'completed': len(completed),
        'errors': len([r for r in results if r['status'] == 'error']),
        'duration_match_rate': duration_matches / len(completed) if completed else 0,
        'results': results
    }


# Test definitions for evaluator
GOLD_SET_TESTS = [
    {
        'name': 'gold_set_all',
        'description': 'Generate synthetic versions of all gold standard phrases',
        'test_function': test_gold_set_generation
    }
]
