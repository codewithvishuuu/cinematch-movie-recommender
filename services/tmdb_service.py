"""TMDB service layer: movie discovery, details, posters, trailers.

Reliability rules enforced here (Phase 2):
- All HTTP traffic goes through ``services.tmdb_client`` (Session + retries).
- The API key is never read or logged in this module.
- We NEVER fabricate movie metadata. If TMDB is unreachable or the key is
  invalid, real local dataset values are used and marked ``source: local``.
- Static fallbacks never overwrite a movie's real title (sequels keep their
  names: "Toy Story 2", "The Dark Knight Rises", ...).
- List endpoints (trending/popular/top-rated) reuse the movie IDs returned by
  TMDB instead of re-searching every title (removes the N+1 pattern).
- Cached payloads are keyed by API status so stale/unreachable results are
  never served after the key becomes valid.
"""
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from config import settings
from services.tmdb_client import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TMDBUnavailable,
    cache_status_token,
    get_api_status,
    get_client,
    is_valid_trailer_url,
    STATUS_CONNECTED,
)

logger = logging.getLogger("cinematch.tmdb")

# ---------------------------------------------------------------------------
# Real image/trailer assets for well-known titles, used ONLY as a visual hint
# in offline mode. Contains no fabricated metadata (no ratings, dates or
# synopses are invented anywhere else in this module).
# ---------------------------------------------------------------------------
LOCAL_ASSET_HINTS = {
    "interstellar": {
        "poster_path": "gEU2QvJWzIF7OIvJ2QJICm65mqj",
        "backdrop_path": "xJHok76cNjUmxwqHQEBnmDdh8jL",
        "trailer_key": "zSWdZVtXT7E",
    },
    "inception": {
        "poster_path": "o01wJy9SKkRkiJCt5ld8a91Zu7",
        "backdrop_path": "s3Tld83hsw34W36koMs2k0t0gH1",
        "trailer_key": "YoHD9XEInc0",
    },
    "heat": {
        "poster_path": "rrbgQ4v74I5nz1031Wr6e68948v",
        "backdrop_path": "l6cl2L23t46iF7hScCKMW0wOI0z",
        "trailer_key": "2GffdYGRyjY",
    },
    "toy story": {
        "poster_path": "uXDfjJbdP4ijW5hWSBrPrlK7697",
        "backdrop_path": "3RfvcheiRSTUrR7gdOCTtXUi4Yl",
        "trailer_key": "v-PjgYDrgOP",
    },
    "toy story 2": {
        "poster_path": "2MFIeZUkjo9l3juHePDfXrOXpfF",
        "backdrop_path": "mcqu6eAGViam0mxNnDWUTLUfcQH",
        "trailer_key": "g2JPYjjcXiE",
    },
    "the avengers": {
        "poster_path": "RYMX2wc76MQUgJmqLJICjNV2nF",
        "backdrop_path": "9BBGoGgA74j2qgja6ZPPPHi644B",
        "trailer_key": "eOrNdByGMv8",
    },
    "the dark knight": {
        "poster_path": "qJ2tW6WMUDux911r6m7haRef0WH",
        "backdrop_path": "cfT29Im5VDvjE0RpyKOSdCKZal7",
        "trailer_key": "EXeTwQWrcwY",
    },
    "the dark knight rises": {
        "poster_path": "tHLdH3YKc1oamnMr2K4wQ9dfPB3",
        "backdrop_path": "dKxkwAJfZVfcLWJQDdxD4udYENI",
        "trailer_key": "GokKUqLcvD8",
    },
    "gladiator": {
        "poster_path": "ty8hDC7mG3ADc0g0g4Xn6i6gf1v",
        "backdrop_path": "b8BE4Fu9c9H95gRyxN645K5m07d",
        "trailer_key": "ol67qo3WhZw",
    },
    "avatar": {
        "poster_path": "kyeqWzo2vY36jyg165gIcn5iFcE",
        "backdrop_path": "vL5f6jA1m7oWciiNGevmQ87jZ65",
        "trailer_key": "5PSNL1q36VY",
    },
    "deadpool": {
        "poster_path": "378X60rKVjJg8tG7568C98858uD",
        "backdrop_path": "h593046kgz5nJvj8xg346w2C51A",
        "trailer_key": "ONHBaC-pfsk",
    },
    "guardians of the galaxy": {
        "poster_path": "r7vmZjiyZw52niBs54Ta8g76Zqp",
        "backdrop_path": "r17XvHQ5cwSR5oF72v1vUqPv2n5",
        "trailer_key": "d96cjJhvlMA",
    },
}

# Official TMDB genre ids (static, real mapping - no fabrication).
TMDB_GENRE_ID_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
}


def _normalize_hint_key(title):
    """Lowercases and strips punctuation/space for asset-hint lookup."""
    if not title or not isinstance(title, str):
        return ""
    return re.sub(r"[^a-z0-9]", "", title.lower().strip())


def _get_asset_hints(title):
    """Returns poster/backdrop/trailer hints for a known title (or empty dict)."""
    key = _normalize_hint_key(title)
    hints = LOCAL_ASSET_HINTS.get(key)
    if hints is None:  # keys with spaces need the raw lowercase title
        hints = LOCAL_ASSET_HINTS.get((title or "").strip().lower())
    return hints or {}


# ---------------------------------------------------------------------------
# Poster / backdrop URL validation
# ---------------------------------------------------------------------------
_BAD_IMAGE_MARKERS = ("placeholder", "no+poster", "no_poster", "notfound", "not+found", "not_found", "null", "none", "na")


def clean_image_url(path, size_prefix, fallback):
    """Builds a valid TMDB image URL, or the fallback image for bad/missing paths.

    Never returns a malformed/broken URL - only a valid image URL or None.
    """
    if not path or not isinstance(path, str):
        return fallback
    stripped = path.strip()
    if not stripped or stripped.lower() in ("null", "none", "/null", "/none", "/null.jpg"):
        return fallback
    if len(stripped) < 5:  # too short to be a real image path
        return fallback
    marker_hit = any(m in stripped.lower() for m in _BAD_IMAGE_MARKERS)
    if marker_hit:
        return fallback
    clean_path = stripped.lstrip("/")
    return f"https://image.tmdb.org/t/p/{size_prefix}/{clean_path}"


# ---------------------------------------------------------------------------
# Local (offline) data - REAL values from the bundled dataset only
# ---------------------------------------------------------------------------
def _local_dataset_row(title):
    """Finds the movie row in the local 45k dataset. Returns a Series or None."""
    try:
        from ml.recommender import df

        if df is None or df.empty:
            return None
        title_norm = title.lower().strip() if isinstance(title, str) else ""
        exact = df[df["title"].astype(str).str.lower().str.strip() == title_norm]
        if not exact.empty:
            return exact.iloc[0]
        # secondary: cleaned-title match (punctuation/year stripped)
        if "title_clean" in df.columns:
            clean = re.sub(r"\s*\(\d{4}\)\s*$", "", title_norm)
            clean = re.sub(r"[^\w\s]", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean:
                alt = df[df["title_clean"] == clean]
                if not alt.empty:
                    return alt.iloc[0]
    except Exception as exc:
        logger.debug("Local dataset lookup failed for %r: %s", title, exc.__class__.__name__)
    return None


def _build_local_fallback(title, row=None):
    """Honest offline movie record built from real dataset values.

    - Title is ALWAYS preserved (never overwritten by a canonical name).
    - Rating/genres/overview come from the real bundled dataset when the movie
      is present; nothing is invented.
    - Poster/backdrop/trailer come from known-real assets (hints) or generic
      fallback images. A trailer appears ONLY when a real YouTube key exists.
    """
    if row is None:
        row = _local_dataset_row(title)

    hints = _get_asset_hints(title)

    if row is not None:
        overview = str(row.get("overview") or "").strip()
        from ml.recommender import parse_genres
        genres_raw = str(row.get("genres") or "")
        genres = parse_genres(genres_raw)
        try:
            rating = float(row.get("vote_average"))
        except (TypeError, ValueError):
            rating = None
        if rating == 0.0:
            rating = None  # unrated - never present a fabricated score
        dataset_title = str(row.get("title") or title)
    else:
        overview = "Synopsis unavailable while in offline mode. Connect a valid TMDB API key to load full details."
        genres = []
        rating = None
        dataset_title = title

    trailer = None
    trailer_key = hints.get("trailer_key")
    if trailer_key and re.fullmatch(r"[A-Za-z0-9_-]{11}", trailer_key):
        trailer = f"https://www.youtube.com/watch?v={trailer_key}"

    return {
        "title": dataset_title,
        "poster_url": settings.TMDB_IMAGE_BASE_URL + f"/{settings.POSTER_SIZE_W500}/{hints['poster_path']}"
        if hints.get("poster_path") else settings.DEFAULT_FALLBACK_POSTER,
        "backdrop_url": settings.TMDB_IMAGE_BASE_URL + f"/{settings.BACKDROP_SIZE_ORIGINAL}/{hints['backdrop_path']}"
        if hints.get("backdrop_path") else settings.DEFAULT_FALLBACK_BACKDROP,
        "rating": rating,
        "release_date": settings.UNKNOWN_RELEASE_DATE,  # not stored in the bundled dataset
        "runtime": None,
        "genres": genres,
        "cast": [],
        "overview": overview,
        "trailer_url": trailer,
        "source": "local",
    }


def _get_local_featured_movies(limit=12):
    """Offline trending/popular deck: real popular titles from the local dataset."""
    try:
        from ml.recommender import df

        if df is None or df.empty:
            return []
        import pandas as pd

        work = df.copy()
        work["_pop"] = pd.to_numeric(work["popularity"], errors="coerce").fillna(0.0)
        seen, movies = set(), []
        for _, row in work.sort_values("_pop", ascending=False).iterrows():
            t = str(row["title"])
            if t.lower() in seen:
                continue
            seen.add(t.lower())
            movies.append(_build_local_fallback(t, row))
            if len(movies) >= limit:
                break
        return movies
    except Exception as exc:
        logger.debug("Local featured movies failed: %s", exc.__class__.__name__)
        return []


# ---------------------------------------------------------------------------
# TMDB payload parsing -> app movie-dict contract (UI-compatible)
# ---------------------------------------------------------------------------
def _extract_trailer_url(videos_data):
    """Returns a validated YouTube watch URL or None. Never a bare domain."""
    if not videos_data:
        return None
    for video in videos_data.get("results", []):
        site = str(video.get("site") or "")
        vid_type = str(video.get("type") or "")
        if site.lower() != "youtube":
            continue
        if vid_type not in ("Trailer", "Teaser"):
            continue
        key = str(video.get("key") or "")
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", key):
            return f"https://www.youtube.com/watch?v={key}"
    return None


def _build_movie_dict_from_tmdb(data, fallback_title):
    """Converts a TMDB movie/{id} payload into the shared movie-dict contract."""
    title = data.get("title") or data.get("original_title") or fallback_title
    poster_path = data.get("poster_path")
    backdrop_path = data.get("backdrop_path")
    if not poster_path and backdrop_path:  # backdrop doubles as poster when needed
        poster_path = backdrop_path

    genres = [g.get("name", "") for g in (data.get("genres") or []) if g.get("name")]
    cast = [a.get("name", "") for a in (data.get("credits") or {}).get("cast", [])[:4] if a.get("name")]
    runtime = data.get("runtime") or None
    raw_rating = data.get("vote_average")
    try:
        rating = round(float(raw_rating), 1) if raw_rating is not None else None
    except (TypeError, ValueError):
        rating = None
    if rating == 0.0:
        rating = None

    return {
        "title": title,
        "poster_url": clean_image_url(poster_path, settings.POSTER_SIZE_W500, settings.DEFAULT_FALLBACK_POSTER),
        "backdrop_url": clean_image_url(backdrop_path, settings.BACKDROP_SIZE_ORIGINAL, settings.DEFAULT_FALLBACK_BACKDROP),
        "rating": rating,
        "release_date": data.get("release_date") or settings.UNKNOWN_RELEASE_DATE,
        "runtime": runtime,
        "genres": genres,
        "cast": cast,
        "overview": data.get("overview") or "No synopsis available for this title.",
        "trailer_url": _extract_trailer_url(data.get("videos")),
        "source": "tmdb",
    }


# ---------------------------------------------------------------------------
# Search -> details (title-based, used by recommendation cards)
# ---------------------------------------------------------------------------
def _pick_best_search_match(results, title_norm, year):
    """Priority matching: exact+year, exact, punctuation/roman-normalized, first."""
    if not results:
        return None

    for item in results:
        item_title = str(item.get("title") or "").lower().strip()
        item_year = str(item.get("release_date") or "")[:4]
        if item_title == title_norm and (not year or item_year == str(year)):
            return item
    for item in results:
        if str(item.get("title") or "").lower().strip() == title_norm:
            return item

    q_norm = re.sub(r"\s*\(\d{4}\)\s*$", "", title_norm)
    q_norm = re.sub(r"[^\w\s]", "", q_norm).strip()
    for item in results:
        item_norm = str(item.get("title") or "").lower().strip()
        item_norm = re.sub(r"\s*\(\d{4}\)\s*$", "", item_norm)
        item_norm = re.sub(r"[^\w\s]", "", item_norm).strip()
        if item_norm == q_norm:
            return item

    return results[0]


def _rate_limit_log_throttled():
    """Logs 429 conditions at most once per minute."""
    now = time.monotonic()
    if now - _rate_limit_log_throttled.last >= 60:
        _rate_limit_log_throttled.last = now
        logger.warning("TMDB rate limit exceeded; temporarily serving local dataset data.")
_rate_limit_log_throttled.last = 0.0


def _search_movie_tmdb(title, year=None):
    """Runs the layered TMDB search (with punctuation-cleanup fallback)."""
    client = get_client()
    results = client.search_movie(title, year=year) if year else client.search_movie(title)
    if not results.get("results") and year:
        results = client.search_movie(title)
    if not results.get("results"):
        cleaned = re.sub(r"[^\w\s]", " ", title)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned and cleaned.lower() != title.lower():
            results = client.search_movie(cleaned)
    return results.get("results", [])


@st.cache_data(ttl=86400, show_spinner=False)
def _fetch_movie_details_cached(title, year, status_token):
    """Actual implementation of fetch_movie_details (cache-keyed by API status)."""
    try:
        if status_token != STATUS_CONNECTED:
            return _build_local_fallback(title)

        results = _search_movie_tmdb(title, year=year)
        if not results:
            logger.debug("TMDB search returned no results for %r; using local data.", title)
            return _build_local_fallback(title)

        selected = _pick_best_search_match(results, (title or "").lower().strip(), year)
        if selected is None:
            return _build_local_fallback(title)

        movie_id = selected.get("id")
        if not movie_id:
            return _build_local_fallback(title)

        # Details aggregation with append_to_response videos/credits (one request).
        try:
            data = get_client().movie_details(movie_id)
            return _build_movie_dict_from_tmdb(data, title)
        except NotFoundError:
            # The matched id is gone - retry with the next candidate.
            for alt in results[1:5]:
                alt_id = alt.get("id")
                if not alt_id:
                    continue
                try:
                    data = get_client().movie_details(alt_id)
                    return _build_movie_dict_from_tmdb(data, title)
                except NotFoundError:
                    continue
                except (AuthenticationError, RateLimitError, TMDBUnavailable) as exc:
                    _log_generic_api_issue(exc)
                    return _build_local_fallback(title)
            return _build_local_fallback(title)
    except (AuthenticationError, RateLimitError, TMDBUnavailable) as exc:
        _log_generic_api_issue(exc)
        return _build_local_fallback(title)
    except Exception as exc:  # last line of defense: honest local data, never a crash
        logger.debug("Unexpected TMDB details error for %r: %s", title, exc.__class__.__name__)
        return _build_local_fallback(title)


def _log_generic_api_issue(exc):
    if isinstance(exc, RateLimitError):
        _rate_limit_log_throttled()
    elif isinstance(exc, AuthenticationError):
        logger.error("TMDB authentication failed (invalid or revoked API key).")
    else:
        logger.debug("TMDB request unavailable: %s", exc)


def fetch_movie_details(title, year=None):
    """Returns a movie-dict for ``title`` from TMDB or honest local data.

    Contract (unchanged): title, poster_url, backdrop_url, rating,
    release_date, runtime, genres, cast, overview, trailer_url.
    """
    return _fetch_movie_details_cached(title, year, cache_status_token())


# ---------------------------------------------------------------------------
# List endpoints - by-id (no N+1 search pattern) + bounded concurrency
# ---------------------------------------------------------------------------
def _fetch_details_by_id(movie_id, fallback_title=None):
    """Fetches complete details for a known TMDB movie id (1 request)."""
    try:
        data = get_client().movie_details(movie_id)
        return _build_movie_dict_from_tmdb(data, fallback_title)
    except NotFoundError:
        return None
    except (AuthenticationError, RateLimitError, TMDBUnavailable) as exc:
        _log_generic_api_issue(exc)
        return None
    except Exception as exc:
        logger.debug("Unexpected by-id details error for %s: %s", movie_id, exc.__class__.__name__)
        return None


def _fetch_details_batch(items, workers=8):
    """Fetches details for a list of TMDB result items concurrently."""
    if not items:
        return []

    def one(item):
        title = item.get("title") or item.get("original_title") or item.get("name") or ""
        return _fetch_details_by_id(item.get("id"), title)

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="tmdb") as pool:
        results = list(pool.map(one, items))
    return [r for r in results if r is not None]


@st.cache_data(ttl=86400, show_spinner=False)
def _curated_list_cached(kind, limit, status_token):
    """One cached implementation for trending/popular/top-rated."""
    if status_token != STATUS_CONNECTED:
        return _get_local_featured_movies(limit=limit)

    try:
        client = get_client()
        if kind == "trending":
            items = client.trending_week(limit=20)
        elif kind == "popular":
            items = client.popular(limit=20)
        elif kind == "top_rated":
            items = client.top_rated(limit=20)
        else:
            return []
    except (AuthenticationError, RateLimitError, TMDBUnavailable) as exc:
        _log_generic_api_issue(exc)
        return _get_local_featured_movies(limit=limit)

    movies = _fetch_details_batch(items, workers=8)
    return movies[:limit]


def get_trending_movies(limit=18):
    """Fetches trending movies via TMDB ids (1 list + N detail requests, concurrent)."""
    return _curated_list_cached("trending", limit, cache_status_token())


def get_popular_movies(limit=18):
    """Fetches popular movies via TMDB ids (no search-per-title)."""
    return _curated_list_cached("popular", limit, cache_status_token())


def get_top_rated_movies(limit=18):
    """Fetches top-rated movies via TMDB ids (no search-per-title)."""
    return _curated_list_cached("top_rated", limit, cache_status_token())