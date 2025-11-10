"""
LivePortrait Model Wrapper
High-quality portrait animation from audio + reference image
Optimized for CUDA, faster than SadTalker

Repository: https://github.com/KwaiVGI/LivePortrait
"""
import os
import sys
import time
import torch
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# LivePortrait will be cloned at runtime/LivePortrait
LIVEPORTRAIT_DIR = Path(__file__).parent.parent / "LivePortrait"


class LivePortraitModel:
    """
    LivePortrait wrapper for audio-driven portrait animation
    Optimized for CUDA (NVIDIA GPUs)
    """
    
    def __init__(self):
        self.device = "cuda"  # LivePortrait works best on CUDA
        self.pipeline = None
        self._ready = False
        
    def initialize(self):
        """Initialize LivePortrait pipeline"""
        if self._ready:
            return
            
        start_time = time.time()
        
        try:
            # Add LivePortrait to Python path
            if LIVEPORTRAIT_DIR.exists():
                sys.path.insert(0, str(LIVEPORTRAIT_DIR))
            else:
                raise RuntimeError(f"LivePortrait not found at {LIVEPORTRAIT_DIR}. Run setup script first.")
            
            logger.info(f"Loading LivePortrait on device: {self.device}")
            
            # Import LivePortrait modules
            from src.config.inference_config import InferenceConfig
            from src.config.crop_config import CropConfig
            from src.live_portrait_pipeline import LivePortraitPipeline
            
            # Initialize configs
            inference_cfg = InferenceConfig()
            inference_cfg.device_id = 0 if self.device == "cuda" else -1
            
            crop_cfg = CropConfig()
            
            # Initialize pipeline
            self.pipeline = LivePortraitPipeline(
                inference_cfg=inference_cfg,
                crop_cfg=crop_cfg
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✅ LivePortrait initialized successfully in {elapsed:.2f}s")
            self._ready = True
            
        except Exception as e:
            logger.error(f"Failed to initialize LivePortrait: {e}", exc_info=True)
            raise
    
    def is_ready(self) -> bool:
        """Check if model is initialized"""
        return self._ready and self.pipeline is not None
    
    def generate_video(
        self,
        audio_path: str,
        reference_image_path: str,
        output_path: str,
        fps: int = 25,
        enhancer: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Generate talking head video from audio and reference image
        
        Args:
            audio_path: Path to input audio file (WAV)
            reference_image_path: Path to reference face image
            output_path: Path for output video
            fps: Output video frame rate
            enhancer: Optional face enhancer ('gfpgan' or None)
            
        Returns:
            Tuple of (output_video_path, generation_time_ms)
        """
        if not self._ready:
            raise RuntimeError("LivePortrait model not initialized")
        
        start_time = time.time()
        
        try:
            logger.info(f"Generating video with LivePortrait: audio={audio_path}, image={reference_image_path}")
            
            # Create output directory
            output_dir = Path(output_path).parent
            output_dir.mkdir(exist_ok=True, parents=True)
            
            # LivePortrait expects specific input format
            # Process audio to extract motion features
            from src.utils.audio import extract_audio_features
            audio_features = extract_audio_features(audio_path, fps=fps)
            
            # Load and preprocess source image
            from src.utils.image import load_image_rgb
            source_image = load_image_rgb(reference_image_path)
            
            # Run LivePortrait pipeline
            output_video = self.pipeline.execute(
                source_image=source_image,
                driving_audio_features=audio_features,
                output_path=output_path
            )
            
            # Apply GFPGAN enhancement if requested
            if enhancer == "gfpgan":
                logger.info("Applying GFPGAN face enhancement...")
                from utils.gfpgan_utils import enhance_video
                output_video = enhance_video(output_video, output_path)
            
            generation_time = (time.time() - start_time) * 1000
            logger.info(f"✅ LivePortrait video generated in {generation_time:.0f}ms")
            
            return output_path, generation_time
            
        except Exception as e:
            logger.error(f"LivePortrait generation failed: {e}", exc_info=True)
            raise
    
    def cleanup(self):
        """Cleanup model resources"""
        if self.pipeline:
            del self.pipeline
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self._ready = False
            logger.info("LivePortrait model cleaned up")


# Global instance
_liveportrait_model: Optional[LivePortraitModel] = None


def get_liveportrait_model() -> LivePortraitModel:
    """Get or create global LivePortrait model instance"""
    global _liveportrait_model
    if _liveportrait_model is None:
        _liveportrait_model = LivePortraitModel()
    return _liveportrait_model
