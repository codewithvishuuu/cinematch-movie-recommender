import os
import sys
from dotenv import load_dotenv

# Supported Python runtime guard (the ML artifacts require numpy>=2, which
# requires Python 3.10 or newer).
if sys.version_info < (3, 10):
    raise RuntimeError(
        f"CineMatch requires Python 3.10 or newer (found {sys.version_info.major}.{sys.version_info.minor}). "
        "Please upgrade your Python runtime."
    )

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# API Configuration
# ---------------------------------------------------------------------------
# The TMDB API key is read once here and consumed ONLY by services/tmdb_client.py.
# It is never logged, printed, or rendered in the UI.
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()

# Placeholder values that must never be treated as real keys (e.g. the
# default value shipped inside .env.example).
_PLACEHOLDER_KEYS = {
    "your_tmdb_api_key_here",
    "changeme",
    "change-me",
    "placeholder",
    "replace_me",
    "example",
    "xxx",
    "sk-123",
    "api_key",
    "tmdb_api_key",
    "none",
}

# TMDB Base Endpoints
TMDB_BASE_URL = "https://api.tmdb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# Poster Sizes
POSTER_SIZE_W500 = "w500"
POSTER_SIZE_W185 = "w185"
BACKDROP_SIZE_W1280 = "w1280"
BACKDROP_SIZE_ORIGINAL = "original"

# App Settings
APP_NAME = "CineMatch"
DEFAULT_FALLBACK_POSTER = "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
DEFAULT_FALLBACK_BACKDROP = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1280&auto=format&fit=crop"

# Project defaults for honest fallback metadata when the live API is down.
# These constants are placeholders ONLY: the real fallback values are read
# from the local movie dataset (ml/df.pkl) instead of being fabricated.
UNKNOWN_RELEASE_DATE = "N/A"
UNKNOWN_RUNTIME = None


def is_api_key_configured():
    """Checks whether a syntactically plausible TMDB API key is set.

    This is a cheap, local check only (no network). A non-empty key does
    NOT imply the key is valid - use services.tmdb_client.get_api_status()
    for the live validity check.
    """
    if not TMDB_API_KEY:
        return False
    if TMDB_API_KEY.lower() in _PLACEHOLDER_KEYS:
        return False
    if len(TMDB_API_KEY) < 16:  # real TMDB v3 keys are 32 hex chars
        return False
    return True