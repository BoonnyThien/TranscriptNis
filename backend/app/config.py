"""
Configuration module for the Transcript backend.
Loads environment variables and provides settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# Cloudflare AI Configuration
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "@cf/openai/whisper")

# API URL for Cloudflare Workers AI
CLOUDFLARE_AI_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{WHISPER_MODEL}"

# Validation
def validate_config():
    """Validate required configuration is present."""
    if not CLOUDFLARE_ACCOUNT_ID:
        raise ValueError("CLOUDFLARE_ACCOUNT_ID is required in .env file")
    if not CLOUDFLARE_API_TOKEN:
        raise ValueError("CLOUDFLARE_API_TOKEN is required in .env file")
    return True
