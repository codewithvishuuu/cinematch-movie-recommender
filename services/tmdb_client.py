"""Thin, resilient TMDB REST client.

Responsibilities:
- Own the API key (it is never imported or logged anywhere else).
- Provide a persisting ``requests.Session`` with retries + exponential backoff.
- Classify failures into typed exceptions (auth / rate-limit / not-found /
  network-unavailable) so callers can react honestly instead of fabricating data.
- Report API connectivity status (``get_api_status``) that is cached and is a
  real network check - NOT "key is non-empty".
"""
import logging
import re

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import settings

logger = logging.getLogger("cinematch.tmdb")

# ---------------------------------------------------------------------------
# Typed errors - callers can distinguish failure modes
# ---------------------------------------------------------------------------


class TMDBError(Exception):
    """Base class for all TMDB client errors."""


class TMDBUnavailable(TMDBError):
    """Network unreachable / timeout / 5xx after retries."""


class AuthenticationError(TMDBError):
    """The configured API key was rejected (401/403)."""


class RateLimitError(TMDBError):
    """TMDB rate limit exhausted even after retry/backoff (429)."""


class NotFoundError(TMDBError):
    """The requested endpoint/movie does not exist (404)."""


# ---------------------------------------------------------------------------
# Trailer validation - a trailer is only "real" if it carries a YouTube key
# ---------------------------------------------------------------------------
_YOUTUBE_KEY_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])",
    re.IGNORECASE,
)


def is_valid_trailer_url(url):
    """True only for real YouTube watch URLs with an 11-char video key."""
    if not url or not isinstance(url, str):
        return False
    return bool(_YOUTUBE_KEY_RE.search(url.strip()))


def youtube_key_from_url(url):
    """Extracts the 11-char YouTube key from a validated watch URL (or None)."""
    if not url or not isinstance(url, str):
        return None
    match = _YOUTUBE_KEY_RE.search(url.strip())
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT = (5.0, 10.0)  # (connect, read) seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 0.7  # sleep 0.7s, 1.4s, 2.8s between attempts
_RETRYABLE_STATUS = (429, 500, 502, 503, 504)


class TMDBClient:
    """Stateless-safe HTTP client for the TMDB v3 API."""

    def __init__(self):
        self._key = settings.TMDB_API_KEY
        retry = Retry(
            total=MAX_RETRIES,
            connect=MAX_RETRIES,
            read=MAX_RETRIES,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=_RETRYABLE_STATUS,
            allowed_methods=frozenset(["GET"]),
            respect_retry_after_header=True,  # honor TMDB Retry-After on 429
        )
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        self._session.headers.update({"Accept": "application/json"})

    # -- low level ----------------------------------------------------------

    def get(self, path, params=None, auth_required=True, timeout=DEFAULT_TIMEOUT):
        """Performs a GET against the TMDB base URL.

        ``params`` are merged over the api_key parameter. Raises typed
        exceptions; never returns non-2xx response bodies.
        """
        if auth_required and not settings.is_api_key_configured():
            raise AuthenticationError("No TMDB API key configured.")

        query_params = dict(params or {})
        query_params["api_key"] = self._key
        url = f"{settings.TMDB_BASE_URL}/{path.lstrip('/')}"

        try:
            response = self._session.get(url, params=query_params, timeout=timeout)
        except requests.exceptions.Timeout as exc:
            raise TMDBUnavailable(f"TMDB request timed out for '{path}'.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise TMDBUnavailable(f"TMDB unreachable for '{path}'.") from exc
        except requests.exceptions.RequestException as exc:
            raise TMDBUnavailable(f"TMDB request failed for '{path}': {exc.__class__.__name__}") from exc

        if response.status_code in (401, 403):
            raise AuthenticationError(f"TMDB rejected the API key (HTTP {response.status_code}).")
        if response.status_code == 404:
            raise NotFoundError(f"TMDB resource not found: {path}")
        if response.status_code == 429:
            raise RateLimitError("TMDB rate limit exceeded (HTTP 429).")
        if response.status_code >= 500:
            raise TMDBUnavailable(f"TMDB server error (HTTP {response.status_code}).")

        response.raise_for_status()
        return response.json()

    # -- endpoints ------------------------------------------------------------

    def authentication(self, timeout=(4.0, 6.0)):
        """Cheap key-validity probe: GET /authentication."""
        return self.get("authentication", auth_required=True, timeout=timeout)

    def search_movie(self, query, year=None, language="en-US", include_adult=False, timeout=(5.0, 10.0)):
        params = {
            "query": query,
            "language": language,
            "include_adult": include_adult,
        }
        if year:
            params["year"] = year
        return self.get("search/movie", params=params, timeout=timeout)

    def movie_details(self, movie_id, language="en-US", timeout=(5.0, 10.0)):
        params = {"language": language, "append_to_response": "videos,credits"}
        return self.get(f"movie/{movie_id}", params=params, timeout=timeout)

    def trending_week(self, limit=20, timeout=(5.0, 10.0)):
        data = self.get("trending/movie/week", timeout=timeout)
        return data.get("results", [])[:limit]

    def popular(self, limit=20, timeout=(5.0, 10.0)):
        data = self.get("movie/popular", timeout=timeout)
        return data.get("results", [])[:limit]

    def top_rated(self, limit=20, timeout=(5.0, 10.0)):
        data = self.get("movie/top_rated", timeout=timeout)
        return data.get("results", [])[:limit]


@st.cache_resource(show_spinner=False)
def get_client():
    """Returns the shared, cached TMDB client (single Session per process)."""
    return TMDBClient()


# ---------------------------------------------------------------------------
# API status detection (network-backed, cached)
# ---------------------------------------------------------------------------
STATUS_NONE = "none"              # no key configured at all
STATUS_CONNECTED = "connected"    # key validates against TMDB
STATUS_INVALID = "invalid"        # key present but rejected
STATUS_UNREACHABLE = "unreachable"  # key present but TMDB can't be reached right now


@st.cache_data(ttl=1800, show_spinner=False)  # refreshed every 30 min
def _validate_api_key_cached():
    """Network probe. Returns STATUS_CONNECTED / STATUS_INVALID / STATUS_UNREACHABLE.

    The result is cached so the app does not hit the network on every rerun,
    but the probe is a REAL check - a non-empty key is never enough.
    """
    try:
        get_client().authentication()
        return STATUS_CONNECTED
    except AuthenticationError:
        return STATUS_INVALID
    except RateLimitError:
        logger.warning("TMDB rate limit hit during key validation.")
        return STATUS_UNREACHABLE
    except TMDBUnavailable as exc:
        logger.debug("TMDB unreachable during validation: %s", exc)
        return STATUS_UNREACHABLE
    except Exception as exc:  # defensive: never crash the app on a probe
        logger.debug("Unexpected TMDB validation error: %s", exc.__class__.__name__)
        return STATUS_UNREACHABLE


def get_api_status():
    """Returns one of STATUS_* based on the real key state.

    ``none``            -> no usable key configured (offline local mode).
    ``connected``       -> key validated against TMDB.
    ``invalid``         -> key present but rejected by TMDB.
    ``unreachable``     -> key present, TMDB not reachable at the moment.
    """
    if not settings.is_api_key_configured():
        return STATUS_NONE
    return _validate_api_key_cached()


def cache_status_token():
    """Cache-key token separating API states.

    Used inside ``@st.cache_data`` arguments so that data cached while the
    API was unavailable/invalid is never served after the key becomes valid
    (and vice versa). Updates at most as often as the validation cache.
    """
    return get_api_status()