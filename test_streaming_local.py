#!/usr/bin/env python3
"""
Test streaming conversation endpoint locally or on GCP
Measures TTFF (Time to First Frame) and total processing time
"""
import requests
import time
import sys
import json

# Test configuration
if len(sys.argv) > 1 and sys.argv[1] == "gcp":
    BASE_URL = "http://35.243.218.244:8000"
    print("Testing GCP instance: 35.243.218.244")
else:
    BASE_URL = "http://localhost:8000"
    print("Testing local instance")

AUDIO_FILE = "assets/voice/reference_samples/bruce_en_sample.wav"
LANGUAGE = "en"

def test_streaming():
    """Test streaming endpoint and measure TTFF"""
    url = f"{BASE_URL}/api/v1/conversation/stream"
    
    # Prepare multipart form data
    files = {
        'audio': open(AUDIO_FILE, 'rb'),
    }
    data = {
        'language': LANGUAGE,
    }
    
    print(f"\nSending request to {url}")
    print(f"Audio: {AUDIO_FILE}")
    print(f"Language: {LANGUAGE}")
    print("-" * 60)
    
    start_time = time.time()
    first_chunk_time = None
    transcription_time = None
    llm_time = None
    chunk_count = 0
    
    try:
        # Stream the response
        response = requests.post(
            url,
            files=files,
            data=data,
            stream=True,
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        print("\nReceiving SSE events:")
        print("-" * 60)
        
        # Parse SSE stream
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            
            if line.startswith('event:'):
                event_type = line.split(':', 1)[1].strip()
            elif line.startswith('data:'):
                data_str = line.split(':', 1)[1].strip()
                try:
                    event_data = json.loads(data_str)
                    current_time = time.time() - start_time
                    
                    if event_type == 'transcription':
                        transcription_time = current_time
                        print(f"\n[{current_time:.2f}s] TRANSCRIPTION:")
                        print(f"  Text: {event_data.get('text', '')}")
                        print(f"  Language: {event_data.get('language', '')}")
                        print(f"  Time: {event_data.get('time', 0):.2f}s")
                    
                    elif event_type == 'llm_response':
                        llm_time = current_time
                        print(f"\n[{current_time:.2f}s] LLM RESPONSE:")
                        print(f"  Text: {event_data.get('text', '')}")
                        print(f"  Time: {event_data.get('time', 0):.2f}s")
                    
                    elif event_type == 'video_chunk':
                        chunk_count += 1
                        if first_chunk_time is None:
                            first_chunk_time = current_time
                            print(f"\n[{current_time:.2f}s] ⚡ FIRST VIDEO CHUNK (TTFF):")
                        else:
                            print(f"\n[{current_time:.2f}s] VIDEO CHUNK {chunk_count}:")
                        
                        print(f"  Chunk: {event_data.get('chunk_index', 0)}")
                        print(f"  Text: {event_data.get('text_chunk', '')[:60]}...")
                        print(f"  Time: {event_data.get('chunk_time', 0):.2f}s")
                        print(f"  Video: {event_data.get('video_url', '')}")
                    
                    elif event_type == 'complete':
                        print(f"\n[{current_time:.2f}s] ✅ COMPLETE:")
                        print(f"  Total time: {event_data.get('total_time', 0):.2f}s")
                        print(f"  Chunks: {event_data.get('total_chunks', 0)}")
                    
                    elif event_type == 'error':
                        print(f"\n[{current_time:.2f}s] ❌ ERROR:")
                        print(f"  Error: {event_data.get('error', '')}")
                        print(f"  Job ID: {event_data.get('job_id', '')}")
                        return
                
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {data_str[:100]}")
        
        # Print summary
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        if transcription_time:
            print(f"Transcription completed: {transcription_time:.2f}s")
        if llm_time:
            print(f"LLM response completed: {llm_time:.2f}s")
        if first_chunk_time:
            print(f"⚡ TTFF (Time to First Frame): {first_chunk_time:.2f}s")
        print(f"Total chunks generated: {chunk_count}")
        print(f"Total pipeline time: {total_time:.2f}s")
        
        if first_chunk_time:
            improvement = 30 / first_chunk_time  # Assuming 30s blocking time
            print(f"\nEstimated speedup vs blocking: {improvement:.1f}x")
    
    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {e}")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        files['audio'].close()

if __name__ == "__main__":
    test_streaming()
