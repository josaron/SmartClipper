"""Application configuration."""
import os

# Base directory (backend folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Temp and output directories - use environment variables with local fallbacks
TEMP_DIR = os.getenv("TEMP_DIR", os.path.join(BASE_DIR, "temp"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(BASE_DIR, "output"))
VOICES_DIR = os.getenv("VOICES_DIR", os.path.join(BASE_DIR, "voices"))

# Ensure directories exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(VOICES_DIR, exist_ok=True)
