"""
Evaluator main runner
Executes test scenarios and generates metrics reports
"""
import asyncio
import httpx
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List

from scenarios.phase1_tests import Phase1TestScenarios
from scenarios.language_tests import LanguageTestScenarios
from scenarios.gold_set_tests import load_gold_phrases
from metrics.latency import calculate_latency_metrics
from metrics.voice_quality import calculate_voice_metrics
from metrics.language import calculate_language_metrics, detect_language_from_text
from metrics.lip_sync import calculate_lip_sync_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
RUNTIME_URL = os.getenv('RUNTIME_URL', 'http://localhost:8000')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './outputs')
REFERENCE_AUDIO_DIR = os.getenv('REFERENCE_AUDIO_DIR', '/app/assets/voice/reference_samples')

# Performance thresholds
MAX_SUITE_RUNTIME_S = 600  # 10 minutes - warn if evaluator suite exceeds this


class Evaluator:
    """Main evaluator class"""
    
    def __init__(self, runtime_url: str = RUNTIME_URL):
        self.runtime_url = runtime_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout
        
    async def check_runtime_health(self) -> bool:
        """Check if runtime service is healthy"""
        try:
            response = await self.client.get(f"{self.runtime_url}/health")
            health = response.json()
            logger.info(f"Runtime health: {health}")
            # Accept both 'healthy' and 'initializing' status (models load on first request)
            return health.get('status') in ['healthy', 'initializing']
        except Exception as e:
            logger.error(f"Failed to check runtime health: {e}")
            return False
    
    async def run_generation(self, scenario: Dict) -> Dict:
        """
        Run a single generation scenario.
        
        Args:
            scenario: Test scenario dictionary
            
        Returns:
            Result dictionary with metrics
        """
        scenario_id = scenario.get('id', 'unknown')
        logger.info(f"Running scenario: {scenario_id}")
        
        start_time = time.time()
        
        try:
            # Make generation request
            request_data = {
                'text': scenario['text'],
                'language': scenario['language'],
                'reference_image': scenario.get('reference_image')
            }
            
            response = await self.client.post(
                f"{self.runtime_url}/api/v1/generate",
                json=request_data
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Generation completed for {scenario_id}: {result['status']}")
            
            # Download generated video
            video_url = f"{self.runtime_url}{result['video_url']}"
            video_response = await self.client.get(video_url)
            video_response.raise_for_status()
            
            # Save video locally for analysis
            video_filename = f"{scenario_id}_{result['job_id']}.mp4"
            video_path = os.path.join(OUTPUT_DIR, video_filename)
            with open(video_path, 'wb') as f:
                f.write(video_response.content)
            
            logger.info(f"Video saved: {video_path}")
            
            # Calculate metrics
            metrics = await self.calculate_metrics(
                result=result,
                scenario=scenario,
                video_path=video_path
            )
            
            total_time = time.time() - start_time
            metrics['evaluator_total_time_s'] = total_time
            
            # Print command to view the video
            logger.info(f"✅ {scenario.get('name', scenario_id)} completed in {total_time:.1f}s")
            logger.info(f"📹 View video: open {video_path}")
            
            return {
                'scenario_id': scenario_id,
                'scenario_name': scenario.get('name', scenario_id),
                'status': 'success',
                'result': result,
                'metrics': metrics,
                'video_path': video_path
            }
            
        except Exception as e:
            logger.error(f"Scenario {scenario_id} failed: {e}", exc_info=True)
            total_time = time.time() - start_time
            
            # Capture detailed error info for 500s
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'traceback': None
            }
            
            # If it's an HTTP error, try to get response body
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details['status_code'] = e.response.status_code
                    error_details['response_body'] = e.response.text
                    error_details['response_headers'] = dict(e.response.headers)
                except:
                    pass
            
            # Get traceback
            import traceback as tb
            error_details['traceback'] = tb.format_exc()
            
            # Save detailed error log
            self._save_error_log(scenario_id, error_details)
            
            return {
                'scenario_id': scenario_id,
                'scenario_name': scenario.get('name', scenario_id),
                'status': 'failed',
                'error': str(e),
                'error_details': error_details,
                'evaluator_total_time_s': total_time
            }
    
    async def calculate_metrics(
        self,
        result: Dict,
        scenario: Dict,
        video_path: str
    ) -> Dict:
        """
        Calculate all metrics for a generation result.
        
        Args:
            result: Generation result from runtime
            scenario: Test scenario
            video_path: Path to generated video
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        # Latency metrics
        latency_metrics = calculate_latency_metrics(result)
        metrics.update(latency_metrics)
        
        # Language metrics
        expected_lang = scenario['language']
        detected_lang = detect_language_from_text(scenario['text'])
        language_metrics = calculate_language_metrics(
            expected_language=expected_lang,
            detected_language=detected_lang,  # TODO: detect from audio
            text=scenario['text']
        )
        metrics.update(language_metrics)
        
        # Voice quality metrics (if we can access audio file)
        # For now, skip as we don't have direct audio file access
        # TODO: Extract audio from video or get audio path from API
        
        # Lip sync metrics
        # TODO: Need audio path - for now skip
        # lip_sync_metrics = calculate_lip_sync_metrics(video_path, audio_path)
        # metrics.update(lip_sync_metrics)
        
        # Placeholder for missing metrics
        metrics.update({
            'speaker_similarity': 0.0,
            'f0_rmse_hz': 0.0,
            'lip_sync_coherence_0_1': 0.0
        })
        
        return metrics
    
    async def run_phase1_tests(self) -> List[Dict]:
        """Run all Phase 1 test scenarios"""
        logger.info("=== Running Phase 1 Tests ===")
        
        scenarios = Phase1TestScenarios.get_scenarios()
        results = []
        
        for scenario in scenarios:
            result = await self.run_generation(scenario)
            results.append(result)
            
            # Save individual result
            self.save_result(result)
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        return results
    
    async def run_language_tests(self) -> List[Dict]:
        """Run multilingual test scenarios"""
        logger.info("=== Running Language Tests ===")
        
        language_scenarios = LanguageTestScenarios.get_scenarios()
        results = []
        
        for lang_scenario in language_scenarios:
            scenario_results = []
            
            for test in lang_scenario['tests']:
                test['id'] = f"{lang_scenario['id']}_{test['language']}"
                test['name'] = f"{lang_scenario['name']} - {test['language']}"
                
                result = await self.run_generation(test)
                scenario_results.append(result)
                
                # Save individual result
                self.save_result(result)
                
                await asyncio.sleep(2)
            
            results.extend(scenario_results)
        
        return results
    
    async def run_gold_set_tests(self) -> List[Dict]:
        """Run gold standard comparison tests"""
        logger.info("=== Running Gold Set Tests ===")
        
        phrases = load_gold_phrases()
        
        if not phrases:
            logger.warning("No gold standard phrases found - skipping gold set tests")
            return []
        
        logger.info(f"Found {len(phrases)} gold standard phrases")
        results = []
        
        for phrase in phrases:
            # Convert phrase to scenario format
            scenario = {
                'id': f"gold_{phrase['id']}",
                'name': f"Gold Set: {phrase['id']}",
                'text': phrase['text'],
                'language': phrase['language'],
                'reference_image': 'bruce_haircut_small.jpg',  # Use available image
                'gold_clip_path': phrase.get('clip_path'),
                'gold_duration': phrase.get('duration'),
                'difficulty': phrase.get('difficulty')
            }
            
            result = await self.run_generation(scenario)
            results.append(result)
            
            # Save individual result
            self.save_result(result)
            
            await asyncio.sleep(2)
        
        return results
    
    def _save_error_log(self, scenario_id: str, error_details: Dict):
        """Save detailed error information to dedicated error log"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        error_log_path = os.path.join(OUTPUT_DIR, 'error_logs.jsonl')
        
        error_entry = {
            'timestamp': timestamp,
            'scenario_id': scenario_id,
            **error_details
        }
        
        # Append to error log file (JSONL format)
        with open(error_log_path, 'a') as f:
            f.write(json.dumps(error_entry) + '\n')
        
        logger.error(f"Detailed error saved to {error_log_path}")
    
    def save_result(self, result: Dict):
        """Save individual test result to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        scenario_id = result.get('scenario_id', 'unknown')
        
        filename = f"{timestamp}_{scenario_id}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Result saved: {filepath}")
    
    def generate_summary_report(self, all_results: List[Dict], suite_runtime_s: float = 0):
        """Generate summary report of all tests"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"summary_report_{timestamp}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Calculate aggregate statistics
        successful = [r for r in all_results if r['status'] == 'success']
        failed = [r for r in all_results if r['status'] == 'failed']
        
        # Analyze failures
        error_summary = self._analyze_failures(failed)
        
        summary = {
            'timestamp': timestamp,
            'total_tests': len(all_results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(all_results) if all_results else 0,
            'suite_runtime_s': suite_runtime_s,
            'tests_per_minute': (len(all_results) / suite_runtime_s * 60) if suite_runtime_s > 0 else 0,
            'avg_test_duration_s': suite_runtime_s / len(all_results) if all_results else 0,
            'error_summary': error_summary,
            'aggregate_metrics': self.calculate_aggregate_metrics(successful),
            'results': all_results
        }
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary report saved: {filepath}")
        logger.info(f"Success rate: {summary['success_rate']:.1%} ({len(successful)}/{len(all_results)})")
        
        return summary
    
    def _analyze_failures(self, failed_results: List[Dict]) -> Dict:
        """Analyze failed tests and group by error type"""
        if not failed_results:
            return {'has_failures': False}
        
        error_groups = {}
        status_500_errors = []
        
        for result in failed_results:
            error_details = result.get('error_details', {})
            error_msg = result.get('error', 'Unknown error')
            
            # Check for 500 errors
            if error_details.get('status_code') == 500:
                status_500_errors.append({
                    'scenario': result['scenario_name'],
                    'response_body': error_details.get('response_body', 'N/A')
                })
            
            # Group by error type
            error_type = error_details.get('error_type', 'Unknown')
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(result['scenario_name'])
        
        return {
            'has_failures': True,
            'total_failures': len(failed_results),
            'status_500_count': len(status_500_errors),
            'status_500_errors': status_500_errors,
            'error_groups': error_groups,
            'critical': len(status_500_errors) > 0 or len(failed_results) > len(failed_results) * 0.5
        }
    
    def calculate_aggregate_metrics(self, results: List[Dict]) -> Dict:
        """Calculate aggregate statistics across all successful results"""
        if not results:
            return {}
        
        # Collect metrics from all results
        tts_times = []
        avatar_times = []
        total_times = []
        audio_durations = []
        evaluator_times = []
        
        for result in results:
            metrics = result.get('metrics', {})
            if 'tts_ms' in metrics:
                tts_times.append(metrics['tts_ms'])
            if 'avatar_render_ms' in metrics:
                avatar_times.append(metrics['avatar_render_ms'])
            if 'total_generation_ms' in metrics:
                total_times.append(metrics['total_generation_ms'])
            if 'audio_duration_s' in metrics:
                audio_durations.append(metrics['audio_duration_s'])
            if 'evaluator_total_time_s' in metrics:
                evaluator_times.append(metrics['evaluator_total_time_s'])
        
        import numpy as np
        
        return {
            'tts_ms_mean': float(np.mean(tts_times)) if tts_times else 0,
            'tts_ms_std': float(np.std(tts_times)) if tts_times else 0,
            'avatar_render_ms_mean': float(np.mean(avatar_times)) if avatar_times else 0,
            'avatar_render_ms_std': float(np.std(avatar_times)) if avatar_times else 0,
            'total_generation_ms_mean': float(np.mean(total_times)) if total_times else 0,
            'total_generation_ms_std': float(np.std(total_times)) if total_times else 0,
            'audio_duration_s_mean': float(np.mean(audio_durations)) if audio_durations else 0,
            'evaluator_time_s_mean': float(np.mean(evaluator_times)) if evaluator_times else 0,
            'evaluator_time_s_std': float(np.std(evaluator_times)) if evaluator_times else 0,
            'evaluator_time_s_min': float(np.min(evaluator_times)) if evaluator_times else 0,
            'evaluator_time_s_max': float(np.max(evaluator_times)) if evaluator_times else 0,
            'total_evaluator_time_s': float(np.sum(evaluator_times)) if evaluator_times else 0
        }
    
    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()


async def main():
    """Main evaluator entry point"""
    suite_start_time = time.time()
    logger.info("=== Realtime Avatar Evaluator ===")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Initialize evaluator
    evaluator = Evaluator(runtime_url=RUNTIME_URL)
    
    try:
        # Check runtime health
        logger.info(f"Checking runtime at {RUNTIME_URL}...")
        healthy = await evaluator.check_runtime_health()
        
        if not healthy:
            logger.error("Runtime service is not healthy. Waiting 30s...")
            await asyncio.sleep(30)
            healthy = await evaluator.check_runtime_health()
            
            if not healthy:
                logger.error("Runtime service still not healthy. Exiting.")
                return
        
        logger.info("Runtime service is healthy. Starting tests...")
        
        # Run all tests
        all_results = []
        
        # Phase 1 tests (only short texts for CPU mode)
        phase1_results = await evaluator.run_phase1_tests()
        all_results.extend(phase1_results)
        
        # Language tests - DISABLED (too complex for now)
        # language_results = await evaluator.run_language_tests()
        # all_results.extend(language_results)
        
        # Gold set tests - now enabled with GPU acceleration
        gold_set_results = await evaluator.run_gold_set_tests()
        all_results.extend(gold_set_results)
        
        # Calculate total suite runtime
        total_suite_runtime_s = time.time() - suite_start_time
        
        # Generate summary report
        summary = evaluator.generate_summary_report(all_results, total_suite_runtime_s)
        
        logger.info("=== Evaluation Complete ===")
        logger.info(f"Total tests: {summary['total_tests']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success rate: {summary['success_rate']:.1%}")
        logger.info(f"Suite runtime: {total_suite_runtime_s:.1f}s ({total_suite_runtime_s/60:.1f} min)")
        
        # Warn if suite is slow
        if total_suite_runtime_s > MAX_SUITE_RUNTIME_S:
            logger.warning(f"⚠️  Evaluator suite exceeded {MAX_SUITE_RUNTIME_S}s threshold! Consider optimizing slow tests.")
        
        # Critical failure detection
        error_summary = summary.get('error_summary', {})
        if error_summary.get('has_failures'):
            logger.error("\n" + "="*80)
            logger.error("❌ CRITICAL: EVALUATOR FAILURES DETECTED")
            logger.error("="*80)
            logger.error(f"Total failures: {error_summary['total_failures']}")
            logger.error(f"500 errors: {error_summary['status_500_count']}")
            
            if error_summary['status_500_count'] > 0:
                logger.error("\n500 Error Details:")
                for err in error_summary['status_500_errors']:
                    logger.error(f"  - {err['scenario']}: {err['response_body'][:200]}")
                logger.error(f"\nFull error details saved to: {OUTPUT_DIR}/error_logs.jsonl")
            
            logger.error("\nError groups:")
            for error_type, scenarios in error_summary.get('error_groups', {}).items():
                logger.error(f"  {error_type}: {', '.join(scenarios)}")
            
            # Exit with failure if >50% tests failed or any 500 errors
            failure_rate = error_summary['total_failures'] / summary['total_tests']
            if failure_rate > 0.5:
                logger.error(f"\n❌ CRITICAL: >50% test failure rate ({failure_rate:.1%})")
                logger.error("Evaluator suite is fundamentally broken. Fix errors before continuing.")
                import sys
                sys.exit(1)
            elif error_summary['status_500_count'] > 0:
                logger.error(f"\n❌ CRITICAL: {error_summary['status_500_count']} server errors (500) detected")
                logger.error("Server is returning errors. Investigate and fix before continuing.")
                import sys
                sys.exit(1)
        
        # Print all video paths for easy viewing
        logger.info("\n=== Generated Videos ===")
        for result in all_results:
            if result['status'] == 'success':
                video_path = result.get('video_path', 'N/A')
                logger.info(f"open {video_path}  # {result['scenario_name']}")
        
    finally:
        await evaluator.close()


if __name__ == "__main__":
    asyncio.run(main())
