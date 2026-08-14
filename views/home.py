import logging
import random
import streamlit as st
from services.tmdb_service import get_trending_movies, get_popular_movies, get_top_rated_movies, fetch_movie_details
from ml.recommender import df
from components.ui import (
    render_movie_card,
    render_details_overlay_panel,
    render_active_trailer_embed,
    render_section_header,
    render_skeleton_cards,
)
from components.movie_hero import render_movie_hero

logger = logging.getLogger("cinematch.home")

# Section metadata: title, subtitle (presentation only - data comes from services)
SECTION_SUBTITLES = {
    "Trending This Week": "What everyone is streaming right now",
    "Top Rated Masterpieces": "The finest storytelling, ranked by critics",
    "Popular Now": "Most-watched titles across the platform",
    "Sci-Fi Universe": "Journeys beyond the stars",
    "Comedy Picks": "Guaranteed laughs, take your pick",
    "Horror Collection": "Not for the faint of heart",
    "Romance Stories": "Love stories that stay with you",
}

HOME_SECTIONS = [
    ("Trending This Week", "trending"),
    ("Top Rated Masterpieces", "top_rated"),
    ("Popular Now", "popular"),
    ("Sci-Fi Universe", "scifi"),
    ("Comedy Picks", "comedy"),
    ("Horror Collection", "horror"),
    ("Romance Stories", "romance"),
]

STANDOUT_TITLES = ["Interstellar", "Inception", "The Dark Knight"]


def get_genre_movies(genre_name, limit=12):
    """Filters local 45k dataset for top movies in a given genre and aggregates details."""
    if df.empty:
        return []
    try:
        # Case insensitive substring search
        genre_df = df[df['genres'].fillna('').str.lower().str.contains(genre_name.lower())]
        # Sort by popularity and extract best items
        top_genre = genre_df.sort_values(by='popularity', ascending=False).head(limit)

        movies = []
        for _, row in top_genre.iterrows():
            details = fetch_movie_details(row['title'])
            if details:
                movies.append(details)
        return movies
    except Exception as e:
        logger.debug("Error filtering local genre '%s': %s", genre_name, e)
        return []


def _load_home_catalog():
    """Fetches the home catalogs (trending/popular/top-rated/genres)."""
    trending = get_trending_movies(limit=6)
    popular = get_popular_movies(limit=6)
    top_rated = get_top_rated_movies(limit=6)
    scifi = get_genre_movies("Science", limit=6)
    comedy = get_genre_movies("Comedy", limit=6)
    horror = get_genre_movies("Horror", limit=6)
    romance = get_genre_movies("Romance", limit=6)
    return {
        "trending": trending,
        "popular": popular,
        "top_rated": top_rated,
        "scifi": scifi,
        "comedy": comedy,
        "horror": horror,
        "romance": romance,
    }


def render_home_view():
    """Renders the CineMatch cinematic landing view."""
    # 0. Active spotlight drawers and video overlays
    if st.session_state.get("active_trailer_movie"):
        render_active_trailer_embed()
        st.markdown("---")

    if st.session_state.get("selected_movie_details"):
        render_details_overlay_panel()
        st.markdown("---")

    # 1. First visit: show skeleton placeholders, load once, then re-render.
    catalog = st.session_state.get("home_catalog")
    if catalog is None:
        render_skeleton_cards(5)
        st.markdown("<br>", unsafe_allow_html=True)
        render_skeleton_cards(5)
        st.markdown("<br>", unsafe_allow_html=True)
        render_skeleton_cards(5)

        with st.spinner("Loading cinematic catalogs…"):
            catalog = _load_home_catalog()

        st.session_state.home_catalog = catalog
        if not catalog["popular"]:
            st.warning("⚠️ High-fidelity assets loading. Stand by.")
        st.rerun()
        return

    popular = catalog.get("popular", [])
    genre_map = {title: catalog.get(key, []) for title, key in HOME_SECTIONS}

    if not popular:
        return

    # 2. Pinned Hero Spotlight Blockbuster
    if "hero_movie" not in st.session_state or not st.session_state.hero_movie:
        fav_heroes = [m for m in popular if m.get("title") in STANDOUT_TITLES]
        st.session_state.hero_movie = fav_heroes[0] if fav_heroes else random.choice(popular[:3])

    render_movie_hero(st.session_state.hero_movie)

    # 3. Cinematic Category Rows (presentation: 5 premium cards per row)
    for title, _key in HOME_SECTIONS:
        movie_list = genre_map.get(title, [])
        if not movie_list:
            continue

        render_section_header(title, SECTION_SUBTITLES.get(title))

        cols = st.columns(5, gap="medium")
        for idx, movie in enumerate(movie_list[:5]):
            with cols[idx]:
                render_movie_card(movie, key_prefix=f"row_{title[:4]}_{idx}")

        st.markdown("<br>", unsafe_allow_html=True)