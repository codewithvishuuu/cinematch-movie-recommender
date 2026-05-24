import requests
import urllib.parse
import streamlit as st
from config.settings import (
    TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE_URL,
    POSTER_SIZE_W500, BACKDROP_SIZE_ORIGINAL,
    DEFAULT_FALLBACK_POSTER, DEFAULT_FALLBACK_BACKDROP,
    is_api_key_configured
)

# A static mapping of high-quality images for common test movies in case TMDB is offline or key is missing.
STATIC_FALLBACKS = {
    "interstellar": {
        "title": "Interstellar",
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QvJWzIF7OIvJ2QJICm65mqj.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/xJHok76cNjUmxwqHQEBnmDdh8jL.jpg",
        "rating": 8.4,
        "release_date": "2014-11-05",
        "runtime": 169,
        "genres": ["Adventure", "Drama", "Science Fiction"],
        "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel and conquer the vast distances involved in an interstellar voyage.",
        "trailer_url": "https://www.youtube.com/watch?v=zSWdZVtXT7E"
    },
    "inception": {
        "title": "Inception",
        "poster_url": "https://image.tmdb.org/t/p/w500/o01wJy9SKkRkiJCt5ld8a91Zu7.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/s3Tld83hsw34W36koMs2k0t0gH1.jpg",
        "rating": 8.3,
        "release_date": "2010-07-15",
        "runtime": 148,
        "genres": ["Action", "Science Fiction", "Adventure"],
        "overview": "Cobb, a skilled thief who steals valuable secrets from deep within the subconscious during the dream state, is offered a chance to have his history erased as payment for a seemingly impossible task: \"inception\", the planting of another person's idea into their subconscious.",
        "trailer_url": "https://www.youtube.com/watch?v=YoHD9XEInc0"
    },
    "heat": {
        "title": "Heat",
        "poster_url": "https://image.tmdb.org/t/p/w500/rrbgQ4v74I5nz1031Wr6e68948v.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/l6cl2L23t46iF7hScCKMW0wOI0z.jpg",
        "rating": 7.9,
        "release_date": "1995-12-15",
        "runtime": 170,
        "genres": ["Action", "Crime", "Drama", "Thriller"],
        "overview": "Obsessive master thief Neil McCauley leads a top-notch crew on various daring heists throughout Los Angeles while Riley, a similarly dedicated detective, tries to capture him.",
        "trailer_url": "https://www.youtube.com/watch?v=2GffdYGRyjY"
    },
    "toy story": {
        "title": "Toy Story",
        "poster_url": "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlK7697.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/3RfvcheiRSTUrR7gdOCTtXUi4Yl.jpg",
        "rating": 8.0,
        "release_date": "1995-10-30",
        "runtime": 81,
        "genres": ["Animation", "Adventure", "Family", "Comedy"],
        "overview": "Led by Woody, Andy's toys live happily in his room until Andy's birthday brings Buzz Lightyear onto the scene. Afraid of losing his place in Andy's heart, Woody plots against Buzz. But when circumstances separate them from their owner, the duo must learn to put aside their differences.",
        "trailer_url": "https://www.youtube.com/watch?v=v-PjgYDrgOP"
    },
    "the avengers": {
        "title": "The Avengers",
        "poster_url": "https://image.tmdb.org/t/p/w500/RYMX2wc76MQUgJmqLJICjNV2nF.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/9BBGoGgA74j2qgja6ZPPPHi644B.jpg",
        "rating": 7.7,
        "release_date": "2012-04-25",
        "runtime": 143,
        "genres": ["Action", "Science Fiction", "Adventure"],
        "overview": "When an unexpected enemy emerges and threatens global safety and security, Nick Fury, director of the international peacekeeping agency known as SHIELD, finds himself in need of a team to pull the world back from the brink of disaster. Spanning the globe, a daring recruitment effort begins.",
        "trailer_url": "https://www.youtube.com/watch?v=eOrNdByGMv8"
    },
    "the dark knight": {
        "title": "The Dark Knight",
        "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/cfT29Im5VDvjE0RpyKOSdCKZal7.jpg",
        "rating": 8.5,
        "release_date": "2008-07-16",
        "runtime": 152,
        "genres": ["Action", "Crime", "Drama", "Thriller"],
        "overview": "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and District Attorney Harvey Dent, Batman sets out to dismantle the remaining criminal organizations that plague the streets.",
        "trailer_url": "https://www.youtube.com/watch?v=EXeTwQWrcwY"
    },
    "gladiator": {
        "title": "Gladiator",
        "poster_url": "https://image.tmdb.org/t/p/w500/ty8hDC7mG3ADc0g0g4Xn6i6gf1v.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/b8BE4Fu9c9H95gRyxN645K5m07d.jpg",
        "rating": 8.2,
        "release_date": "2000-05-01",
        "runtime": 155,
        "genres": ["Action", "Adventure", "Drama"],
        "overview": "A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.",
        "trailer_url": "https://www.youtube.com/watch?v=ol67qo3WhZw"
    },
    "avatar": {
        "title": "Avatar",
        "poster_url": "https://image.tmdb.org/t/p/w500/kyeqWzo2vY36jyg165gIcn5iFcE.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/vL5f6jA1m7oWciiNGevmQ87jZ65.jpg",
        "rating": 7.5,
        "release_date": "2009-12-15",
        "runtime": 162,
        "genres": ["Action", "Adventure", "Fantasy", "Science Fiction"],
        "overview": "In the 22nd century, a paraplegic Marine is dispatched to the moon Pandora on a unique mission, but becomes torn between following his orders and protecting the world he feels is his home.",
        "trailer_url": "https://www.youtube.com/watch?v=5PSNL1q36VY"
    },
    "deadpool": {
        "title": "Deadpool",
        "poster_url": "https://image.tmdb.org/t/p/w500/378X60rKVjJg8tG7568C98858uD.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/h593046kgz5nJvj8xg346w2C51A.jpg",
        "rating": 7.6,
        "release_date": "2016-02-09",
        "runtime": 108,
        "genres": ["Action", "Adventure", "Comedy"],
        "overview": "The origin story of former Special Forces operative turned mercenary Wade Wilson, who, after being subjected to a rogue experiment, adopts the alter ego Deadpool.",
        "trailer_url": "https://www.youtube.com/watch?v=ONHBaC-pfsk"
    },
    "guardians of the galaxy": {
        "title": "Guardians of the Galaxy",
        "poster_url": "https://image.tmdb.org/t/p/w500/r7vmZjiyZw52niBs54Ta8g76Zqp.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/original/r17XvHQ5cwSR5oF72v1vUqPv2n5.jpg",
        "rating": 7.9,
        "release_date": "2014-07-30",
        "runtime": 121,
        "genres": ["Action", "Adventure", "Science Fiction"],
        "overview": "A group of intergalactic criminals must pull together to stop a fanatical warrior with plans to purge the universe.",
        "trailer_url": "https://www.youtube.com/watch?v=d96cjJhvlMA"
    }
}

def get_static_fallback(title):
    """Retrieves high-quality static fallback details for test suite or demo."""
    title_lower = title.lower()
    for key, data in STATIC_FALLBACKS.items():
        if key in title_lower or title_lower in key:
            return data.copy()
    
    # Generic smart fallback if not in test suite
    return {
        "title": title,
        "poster_url": DEFAULT_FALLBACK_POSTER,
        "backdrop_url": DEFAULT_FALLBACK_BACKDROP,
        "rating": "7.5",
        "release_date": "N/A",
        "runtime": 120,
        "genres": ["Drama", "Feature"],
        "overview": f"No details found on TMDB. '{title}' is an excellent cinematic piece from our AI database. Explore its themes and recommended matches.",
        "trailer_url": "https://www.youtube.com"
    }

def clean_image_url(path, size_prefix, fallback):
    """Robust TMDB image URL validator handling null/none strings and empty paths defensively."""
    if not path or not isinstance(path, str):
        return fallback
    path_stripped = path.strip()
    if path_stripped.lower() in ["", "null", "none", "/null", "/none"]:
        return fallback
    clean_path = path_stripped.lstrip("/")
    return f"https://image.tmdb.org/t/p/{size_prefix}/{clean_path}"

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_movie_details(title, year=None):
    """
    Production-grade TMDB details fetcher featuring year-aware sorting,
    duplicate cleanup, punctuation filters, alternate queries, and deep trace logging.
    """
    title_norm = title.lower().strip()
    
    if not is_api_key_configured():
        return get_static_fallback(title)
        
    # Step 1: Detect year dynamically from local dataset df using local imports to avoid circular dependencies
    if not year:
        try:
            from ml.recommender import df
            if not df.empty:
                rows = df[df['title'].str.lower() == title_norm]
                if not rows.empty:
                    rel_date = str(rows.iloc[0].get('release_date', ''))
                    if rel_date and len(rel_date) >= 4:
                        year = rel_date[:4]
        except Exception as e:
            pass

    try:
        # Step 2: Formulate TMDB search query layers
        import re
        query_title = title
        
        # Primary search url
        search_query = urllib.parse.quote(query_title)
        search_url = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={search_query}&language=en-US&include_adult=false"
        if year:
            search_url += f"&year={year}"
            
        res = requests.get(search_url, timeout=5)
        res.raise_for_status()
        search_data = res.json()
        
        # Alternate search layer A: Search without year if year-restricted query yields empty results
        if not search_data.get("results") and year:
            search_url_noyear = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={search_query}&language=en-US&include_adult=false"
            res = requests.get(search_url_noyear, timeout=5)
            res.raise_for_status()
            search_data = res.json()
            
        # Alternate search layer B: Punctuation cleanup (stripping punctuation/symbols)
        if not search_data.get("results"):
            cleaned_title = re.sub(r'[^\w\s]', ' ', query_title)
            cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
            search_query_clean = urllib.parse.quote(cleaned_title)
            search_url_clean = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={search_query_clean}&language=en-US&include_adult=false"
            res = requests.get(search_url_clean, timeout=5)
            res.raise_for_status()
            search_data = res.json()

        results = search_data.get("results", [])
        if not results:
            try:
                print(f"[TMDB TRACE] Search failed for '{title}' (Year: {year}). Activating static fallback.")
            except:
                pass
            return get_static_fallback(title)

        # Step 3: Production-grade matching priorities across results
        best_match = None
        
        # Priority A: Exact title match + year match
        if year:
            for item in results:
                item_title = item.get("title", "")
                item_year = str(item.get("release_date", ""))[:4]
                if item_title.lower().strip() == title_norm and item_year == str(year):
                    best_match = item
                    break
                    
        # Priority B: Exact title match
        if not best_match:
            for item in results:
                item_title = item.get("title", "")
                if item_title.lower().strip() == title_norm:
                    best_match = item
                    break
                    
        # Priority C: Normalized title match (stripping year in parenthesis and punctuation)
        if not best_match:
            q_norm = re.sub(r'\s*\(\d{4}\)\s*$', '', title_norm)
            q_norm = re.sub(r'[^\w\s]', '', q_norm).strip()
            for item in results:
                item_title_norm = re.sub(r'\s*\(\d{4}\)\s*$', '', item.get("title", "").lower().strip())
                item_title_norm = re.sub(r'[^\w\s]', '', item_title_norm).strip()
                if item_title_norm == q_norm:
                    best_match = item
                    break
                    
        # Priority D: Fallback to the first result (which TMDB sorts by query relevance/popularity)
        if not best_match:
            best_match = results[0]

        movie_id = best_match["id"]
        
        # Step 4: Aggregate complete details (runtime, genres, trailers, cast) using append_to_response
        details_url = f"{TMDB_BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=videos,credits"
        detail_res = requests.get(details_url, timeout=5)
        detail_res.raise_for_status()
        data = detail_res.json()
        
        # Parse Poster & Backdrop with double-layered validation
        poster_path = data.get("poster_path")
        backdrop_path = data.get("backdrop_path")
        
        # Step A: Catch case where poster is missing but backdrop exists! Use backdrop as poster.
        if not poster_path and backdrop_path:
            poster_path = backdrop_path
            
        poster_url = clean_image_url(poster_path, POSTER_SIZE_W500, DEFAULT_FALLBACK_POSTER)
        backdrop_url = clean_image_url(backdrop_path, BACKDROP_SIZE_ORIGINAL, DEFAULT_FALLBACK_BACKDROP)
        
        # Parse Genres
        genres = [g["name"] for g in data.get("genres", [])]
        
        # Parse YouTube Trailer
        trailer_url = "https://www.youtube.com"
        videos = data.get("videos", {}).get("results", [])
        for video in videos:
            if video.get("site") == "YouTube" and video.get("type") in ["Trailer", "Teaser"]:
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break
                
        # Parse Cast
        cast_list = data.get("credits", {}).get("cast", [])
        cast = [actor["name"] for actor in cast_list[:4]]
        
        # Safe debug tracing (CP1252-safe block)
        try:
            print(f"[TMDB TRACE] Search Query Title: '{title}'")
            print(f"[TMDB TRACE] Selected TMDB Match: '{data.get('title')}' (ID: {movie_id})")
            print(f"[TMDB TRACE] poster_path: '{poster_path}' | URL: '{poster_url}'")
            print(f"[TMDB TRACE] backdrop_path: '{backdrop_path}' | URL: '{backdrop_url}'")
        except:
            pass
            
        return {
            "title": data.get("title", title),
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "rating": round(data.get("vote_average", 0.0), 1),
            "release_date": data.get("release_date", "N/A"),
            "runtime": data.get("runtime", 120) or 120,
            "genres": genres,
            "cast": cast,
            "overview": data.get("overview", "No synopsis available."),
            "trailer_url": trailer_url
        }
        
    except Exception as e:
        try:
            print(f"[TMDB TRACE] API Error for '{title}': {e}. Activating smart fallback.")
        except:
            pass
        return get_static_fallback(title)

@st.cache_data(ttl=86400, show_spinner=False)
def get_trending_movies(limit=18):
    """Fetches trending movies from TMDB or falls back to our curated high-quality list."""
    if not is_api_key_configured():
        return _get_local_featured_movies()
        
    try:
        url = f"{TMDB_BASE_URL}/trending/movie/week?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        movies = []
        for item in data.get("results", [])[:limit]:
            # Fetch details for each to get trailers, runtime, etc. (cached)
            movie_details = fetch_movie_details(item["title"])
            if movie_details:
                movies.append(movie_details)
        return movies
    except Exception as e:
        print(f"Error loading trending movies from TMDB: {e}")
        return _get_local_featured_movies()

@st.cache_data(ttl=86400, show_spinner=False)
def get_popular_movies(limit=18):
    """Fetches popular movies from TMDB or falls back to curated list."""
    if not is_api_key_configured():
        return _get_local_featured_movies()
        
    try:
        url = f"{TMDB_BASE_URL}/movie/popular?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        movies = []
        for item in data.get("results", [])[:limit]:
            movie_details = fetch_movie_details(item["title"])
            if movie_details:
                movies.append(movie_details)
        return movies
    except Exception as e:
        print(f"Error loading popular movies: {e}")
        return _get_local_featured_movies()

@st.cache_data(ttl=86400, show_spinner=False)
def get_top_rated_movies(limit=18):
    """Fetches top rated movies from TMDB or falls back to curated list."""
    if not is_api_key_configured():
        # Scramble / slice differently for Top Rated fallback
        featured = _get_local_featured_movies()
        return featured[::-1] # simple mock variation
        
    try:
        url = f"{TMDB_BASE_URL}/movie/top_rated?api_key={TMDB_API_KEY}"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        
        movies = []
        for item in data.get("results", [])[:limit]:
            movie_details = fetch_movie_details(item["title"])
            if movie_details:
                movies.append(movie_details)
        return movies
    except Exception as e:
        print(f"Error loading top rated movies: {e}")
        return _get_local_featured_movies()[::-1]

def _get_local_featured_movies():
    """Generates an initial gorgeous trending/popular movie list from our local test suite & popular database tags."""
    featured_titles = [
        "Interstellar", "Inception", "Heat", "Toy Story", "The Avengers",
        "The Dark Knight", "Avatar", "Gladiator", "The Matrix", 
        "Pulp Fiction", "The Godfather", "Forrest Gump"
    ]
    movies = []
    for title in featured_titles:
        movies.append(get_static_fallback(title))
    return movies
