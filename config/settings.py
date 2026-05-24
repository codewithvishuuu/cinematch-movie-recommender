import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

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

def is_api_key_configured():
    """Checks if a valid-looking TMDB API key is configured."""
    return bool(TMDB_API_KEY) and TMDB_API_KEY != "your_tmdb_api_key_here"
