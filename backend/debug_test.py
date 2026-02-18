"""
Debug script to test transcription with a simple English video.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.audio_downloader import download_audio, _get_ffmpeg_location
from app.services.transcription import transcribe_audio
from app.config import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN

log_file = open("debug_output.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

async def main():
    log("=" * 60)
    log("DEBUG: Transcript API Test (Simple English Video)")
    log("=" * 60)
    
    # Check FFmpeg
    log("\n1. Checking FFmpeg...")
    ffmpeg_loc = _get_ffmpeg_location()
    log(f"   FFmpeg: {ffmpeg_loc}")
    if not ffmpeg_loc:
        log("   [X] FFmpeg not found!")
        return
    
    # Check Cloudflare
    log("\n2. Checking Cloudflare...")
    log(f"   Account ID: {CLOUDFLARE_ACCOUNT_ID[:10]}..." if CLOUDFLARE_ACCOUNT_ID else "   NOT SET")
    log(f"   API Token: {CLOUDFLARE_API_TOKEN[:10]}..." if CLOUDFLARE_API_TOKEN else "   NOT SET")
    
    # Test with a SHORT English-only video (TED-Ed intro, ~1 min)
    test_urls = [
        # Short English video - motivational quote
        "https://www.youtube.com/watch?v=ZXsQAXx_ao0",  # Very short tech video
    ]
    
    for test_url in test_urls:
        log(f"\n3. Testing download: {test_url}")
        try:
            audio_path, metadata = await download_audio(test_url)
            log(f"   [OK] Downloaded: {audio_path.name}")
            log(f"   Platform: {metadata.get('platform')}")
            log(f"   Title: {metadata.get('title', 'N/A')[:50]}")
            file_size = os.path.getsize(audio_path)
            log(f"   File size: {file_size / 1024:.1f} KB")
        except Exception as e:
            log(f"   [X] Download failed: {e}")
            continue
        
        log("\n4. Testing transcription...")
        try:
            result = await transcribe_audio(audio_path)
            log(f"   [OK] Transcription successful!")
            log(f"   Word count: {result['word_count']}")
            log(f"   Text preview: {result['text'][:300]}...")
        except Exception as e:
            log(f"   [X] Transcription failed: {e}")
        
        # Cleanup
        if audio_path.exists():
            os.remove(audio_path)
            log("   [OK] Cleaned up")
        break  # Only test first video
    
    log("\n" + "=" * 60)
    log("Test completed!")
    log_file.close()

if __name__ == "__main__":
    asyncio.run(main())
