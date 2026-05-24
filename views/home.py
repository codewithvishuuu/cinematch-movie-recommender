import streamlit as st
import random
from services.tmdb_service import get_trending_movies, get_popular_movies, get_top_rated_movies, fetch_movie_details
from ml.recommender import df
from components.ui import render_movie_card, render_details_overlay_panel, render_active_trailer_embed
from components.movie_hero import render_movie_hero

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
        print(f"Error filtering local genre '{genre_name}': {e}")
        return []

def render_home_view():
    """Renders the ultimate, premium visually immersive Netflix-style landing view."""
    # 1. Active spotlight drawers and video overlays
    if st.session_state.get("active_trailer_movie"):
        render_active_trailer_embed()
        st.markdown("---")
        
    if st.session_state.get("selected_movie_details"):
        render_details_overlay_panel()
        st.markdown("---")
        
    # 2. Dynamic aggregators fetching (utilizes st.cache_data)
    with st.spinner("Streaming premium cinematic catalogs..."):
        trending = get_trending_movies(limit=6)
        popular = get_popular_movies(limit=6)
        top_rated = get_top_rated_movies(limit=6)
        scifi = get_genre_movies("Science", limit=6) # Sci-Fi Universe
        comedy = get_genre_movies("Comedy", limit=6) # Comedy Picks
        horror = get_genre_movies("Horror", limit=6) # Horror Collection
        romance = get_genre_movies("Romance", limit=6) # Romance Stories
        
    if not popular:
        st.warning("⚠️ High-fidelity assets loading. Stand by.")
        return
        
    # 3. Pinned Hero Spotlight Blockbuster
    if "hero_movie" not in st.session_state or not st.session_state.hero_movie:
        fav_heroes = [m for m in popular if m["title"] in ["Interstellar", "Inception", "The Dark Knight"]]
        st.session_state.hero_movie = fav_heroes[0] if fav_heroes else random.choice(popular[:3])
        
    render_movie_hero(st.session_state.hero_movie)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 4. Cinematic Categories Rows
    sections = [
        ("🔥 Trending This Week", trending),
        ("🏆 Top Rated Masterpieces", top_rated),
        ("🎬 Popular Now", popular),
        ("🚀 Sci-Fi Universe", scifi),
        ("😂 Comedy Picks", comedy),
        ("👻 Horror Collection", horror),
        ("❤️ Romance Stories", romance)
    ]
    
    for title, movie_list in sections:
        if not movie_list:
            continue
            
        st.markdown(f"""
            <div class="section-title-container" style="margin-top: 1.5rem;">
                <h2 style="margin: 0; font-size: 1.6rem; font-family:'Montserrat', sans-serif;">{title}</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Render a gorgeous 6-column snap grid representing the carousel row
        cols = st.columns(6, gap="medium")
        for idx, movie in enumerate(movie_list[:6]):
            with cols[idx]:
                render_movie_card(movie, key_prefix=f"row_{title[:4]}_{idx}")
                
        st.markdown("<br>", unsafe_allow_html=True)
