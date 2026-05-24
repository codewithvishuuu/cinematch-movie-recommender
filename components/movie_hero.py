import streamlit as st
import textwrap
from components.ui import format_runtime

def render_movie_hero(movie):
    """
    Renders an elite, cinematic, animated full-width Spotlight Banner at the top of the Home view.
    Includes validation logic, 4K backdrop overlays, rating/genres taglines, cast details,
    interactive watchlists togglers, and trailer play buttons.
    """
    if not movie:
        return
        
    title = movie.get("title", "Unknown")
    overview = movie.get("overview", "No description available.")
    
    # Backdrop validation
    backdrop_url = movie.get("backdrop_url", "")
    if not backdrop_url or not isinstance(backdrop_url, str) or backdrop_url.lower().strip() in ["", "n/a", "null", "none"]:
        backdrop_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1280&auto=format&fit=crop"
        
    rating = movie.get("rating", "7.5")
    runtime = format_runtime(movie.get("runtime", 120))
    release_date = movie.get("release_date", "N/A")
    year = release_date.split("-")[0] if "-" in release_date else release_date
    
    genres = movie.get("genres", ["Drama", "Feature"])
    genre_tags = " • ".join(genres)
    
    # Cast list formatting
    cast = movie.get("cast", [])
    cast_str = ""
    if cast:
        cast_str = f"<div style='margin-top: 10px; font-size: 0.9rem; color: #ff4d4d; font-weight: 500;'>🎭 Starring: <span style='color: #ffffff;'>{', '.join(cast)}</span></div>"

    # HTML premium spotlight backdrop banner built cleanly without any leading whitespace to completely bypass Markdown code block conversions
    hero_html = (
        "<div class=\"premium-hero\">\n"
        f"<div class=\"premium-hero-backdrop\" style=\"background-image: url('{backdrop_url}');\"></div>\n"
        "<div class=\"premium-hero-overlay\">\n"
        "<span class=\"premium-hero-badge\">🎬 Spotlit blockbuster</span>\n"
        f"<h1 class=\"premium-hero-title\">{title}</h1>\n"
        f"<div class=\"premium-hero-tagline\">{year}  |  ⭐ {rating}/10  |  ⏱️ {runtime}  |  🎬 {genre_tags}</div>\n"
        f"<p class=\"premium-hero-overview\">{overview}</p>\n"
        f"{cast_str}\n"
        "</div>\n"
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # Interactive Action Deck
    cols = st.columns([2.5, 2.5, 7], gap="small")
    has_trailer = movie.get("trailer_url") and "youtube" in movie.get("trailer_url").lower()
    
    with cols[0]:
        if has_trailer:
            if st.button("▶ Watch Trailer", key=f"hero_play_mod_{title.replace(' ', '_')}", use_container_width=True, type="primary"):
                st.session_state.active_trailer_movie = movie
                st.rerun()
        else:
            st.button("🚫 No Trailer", disabled=True, key=f"hero_no_play_mod_{title.replace(' ', '_')}", use_container_width=True)
            
    with cols[1]:
        watchlist = st.session_state.setdefault("watchlist", [])
        is_in_wl = any(w["title"].lower() == title.lower() for w in watchlist)
        
        if is_in_wl:
            if st.button("❌ Remove List", key=f"hero_wl_rem_mod_{title.replace(' ', '_')}", use_container_width=True, type="secondary"):
                st.session_state.watchlist = [w for w in watchlist if w["title"].lower() != title.lower()]
                st.toast(f"Removed '{title}' from watchlist!", icon="🗑️")
                st.rerun()
        else:
            if st.button("➕ Add Watchlist", key=f"hero_wl_add_mod_{title.replace(' ', '_')}", use_container_width=True, type="secondary"):
                st.session_state.watchlist.append(movie)
                st.toast(f"Added '{title}' to watchlist!", icon="💖")
                st.rerun()
