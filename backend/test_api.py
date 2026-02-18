"""
Simple test script for the Transcript API.
Run with: python test_api.py
"""

import httpx
import asyncio

BASE_URL = "http://127.0.0.1:8888"

async def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200

async def test_transcribe(url: str):
    """Test transcribe endpoint"""
    print(f"\nTesting /transcribe with URL: {url}")
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{BASE_URL}/transcribe",
            json={"url": url}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200

async def main():
    print("=" * 50)
    print("Transcript API Test")
    print("=" * 50)
    
    # Test health
    health_ok = await test_health()
    print(f"\n✓ Health check passed: {health_ok}")
    
    # Optional: Test transcription (uncomment and add a short video URL)
    # await test_transcribe("https://www.youtube.com/watch?v=SHORT_VIDEO_ID")
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
