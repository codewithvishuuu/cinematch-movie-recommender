import os
import streamlit as st
import textwrap
from services.tmdb_service import fetch_movie_details

# Base path for main.css
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def inject_netflix_theme():
    """Injects the custom premium Netflix + Letterboxd CSS into the viewport."""
    css_path = os.path.join(BASE_DIR, 'assets', 'main.css')
    try:
        with open(css_path, 'r') as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        print(f"Error loading main.css: {e}")
        # Minimal inline fallback styling
        st.markdown("""
            <style>
            .stApp { background-color: #060608 !important; color: #ffffff !important; }
            h1, h2, h3 { color: #ffffff !important; }
            </style>
        """, unsafe_allow_html=True)

def format_runtime(minutes):
    """Formats runtime integer into readable string e.g. 169 -> 2h 49m."""
    if not minutes or minutes == "N/A":
        return "N/A"
    try:
        hrs = int(minutes) // 60
        mins = int(minutes) % 60
        if hrs > 0:
            return f"{hrs}h {mins}m"
        return f"{mins}m"
    except:
        return f"{minutes} mins"

def render_hero_section(movie):
    """
    Renders an immersive, animated, full-width Netflix hero banner.
    Uses high-fidelity backdrops, radial gradients, metadata and overlay triggers.
    """
    if not movie:
        return
        
    title = movie.get("title", "Unknown")
    overview = movie.get("overview", "No description available.")
    backdrop_url = movie.get("backdrop_url", "")
    if not backdrop_url or not isinstance(backdrop_url, str) or backdrop_url.lower().strip() in ["", "n/a", "null", "none"]:
        backdrop_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1280&auto=format&fit=crop"
        
    rating = movie.get("rating", "N/A")
    runtime = format_runtime(movie.get("runtime", ""))
    release_date = movie.get("release_date", "N/A")
    year = release_date.split("-")[0] if "-" in release_date else release_date
    genres = movie.get("genres", [])
    genre_tags = " • ".join(genres)
    
    # HTML Markup for backdrop background + gradient overlays + details text built cleanly without any leading whitespace to completely bypass Markdown code block conversions
    hero_html = (
        "<div class=\"premium-hero\">\n"
        f"<div class=\"premium-hero-backdrop\" style=\"background-image: url('{backdrop_url}');\"></div>\n"
        "<div class=\"premium-hero-overlay\">\n"
        "<span class=\"premium-hero-badge\">🍿 FEATURED BLOCKBUSTER</span>\n"
        f"<h1 class=\"premium-hero-title\">{title}</h1>\n"
        f"<div class=\"premium-hero-tagline\">{year}  |  ⭐ {rating}/10  |  ⏱️ {runtime}  |  🎬 {genre_tags}</div>\n"
        f"<p class=\"premium-hero-overview\">{overview}</p>\n"
        "</div>\n"
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)
    
    # Interactive CTA controls inside columns immediately below
    cols = st.columns([2.5, 2.5, 7], gap="small")
    has_trailer = movie.get("trailer_url") and "youtube" in movie.get("trailer_url").lower()
    
    with cols[0]:
        if has_trailer:
            if st.button("▶ Watch Trailer", key=f"hero_play_{title}", use_container_width=True, type="primary"):
                st.session_state.active_trailer_movie = movie
                st.rerun()
        else:
            st.button("🚫 No Trailer", disabled=True, key=f"hero_no_play_{title}", use_container_width=True)
            
    with cols[1]:
        watchlist = st.session_state.setdefault("watchlist", [])
        is_in_wl = any(w["title"].lower() == title.lower() for w in watchlist)
        
        if is_in_wl:
            if st.button("❌ Remove List", key=f"hero_wl_rem_{title}", use_container_width=True, type="secondary"):
                st.session_state.watchlist = [w for w in watchlist if w["title"].lower() != title.lower()]
                st.toast(f"Removed '{title}' from watchlist!", icon="🗑️")
                st.rerun()
        else:
            if st.button("➕ Add Watchlist", key=f"hero_wl_add_{title}", use_container_width=True, type="secondary"):
                st.session_state.watchlist.append(movie)
                st.toast(f"Added '{title}' to watchlist!", icon="💖")
                st.rerun()

def render_movie_card(movie, key_prefix="card", relevance_score=None, match_reason=None):
    """
    Renders a premium Netflix movie poster card.
    Displays Match %, ratings, genres, and overlays details / trailer triggers.
    """
    if not movie:
        return
        
    title = movie.get("title", "Unknown")
    poster_url = movie.get("poster_url", "")
    if not poster_url or not isinstance(poster_url, str) or poster_url.lower().strip() in ["", "n/a", "null", "none", "please_enter_your_api_key_here"] or "placeholder" in poster_url.lower() or "no+poster" in poster_url.lower() or "not+found" in poster_url.lower():
        poster_url = "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
        
    rating = movie.get("rating", "N/A")
    release_date = movie.get("release_date", "N/A")
    year = release_date.split("-")[0] if "-" in release_date else release_date
    overview = movie.get("overview", "No synopsis available.")
    
    # Calculate a beautiful realistic Letterboxd Match Percentage
    if relevance_score is not None:
        match_percentage = int(62 + 35 * float(relevance_score))
        match_percentage = min(98, max(55, match_percentage))
        match_badge_html = f'<span class="match-badge">{match_percentage}% MATCH</span>'
    else:
        # Default fallback match percentage for popular items
        match_badge_html = '<span class="match-badge">POPULAR</span>'
        
    # Hidden marker for hover scaling selector
    st.markdown("<div class='movie-card-marker'></div>", unsafe_allow_html=True)
    
    # Render the poster image
    st.image(poster_url, use_container_width=True)
    
    # Render details and meta
    st.markdown(f"""
        <div class="movie-info-panel">
            <div class="movie-card-title" title="{title}">{title}</div>
            <div class="movie-card-meta">
                <span class="rating-badge">⭐ {rating}</span>
                {match_badge_html}
                <span class="year-badge">{year}</span>
            </div>
            <div class="movie-card-overview">{overview}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # AI explanation panel if present
    if match_reason:
        st.markdown(f"""
            <div class="ai-reason-banner">
                🧬 <b>AI Insights:</b> {match_reason}
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
    
    # Subcard buttons
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("ℹ Info", key=f"{key_prefix}_details_{title}", use_container_width=True, type="secondary"):
            st.session_state.selected_movie_details = movie
            st.rerun()
    with c2:
        has_trailer = movie.get("trailer_url") and "youtube" in movie.get("trailer_url").lower()
        if has_trailer:
            if st.button("▶ Play", key=f"{key_prefix}_play_{title}", use_container_width=True, type="secondary"):
                st.session_state.active_trailer_movie = movie
                st.rerun()
        else:
            st.button("🚫", disabled=True, key=f"{key_prefix}_noplay_{title}", use_container_width=True)
    with c3:
        watchlist = st.session_state.setdefault("watchlist", [])
        is_in_wl = any(w["title"].lower() == title.lower() for w in watchlist)
        if is_in_wl:
            if st.button("❤️", key=f"{key_prefix}_wl_{title}", use_container_width=True, type="secondary"):
                st.session_state.watchlist = [w for w in watchlist if w["title"].lower() != title.lower()]
                st.toast(f"Removed '{title}' from watchlist!", icon="🗑️")
                st.rerun()
        else:
            if st.button("➕", key=f"{key_prefix}_wl_{title}", use_container_width=True, type="secondary"):
                st.session_state.watchlist.append(movie)
                st.toast(f"Added '{title}' to watchlist!", icon="💖")
                st.rerun()

def render_details_overlay_panel():
    """
    Renders an immersive detailed Spotlight Panel overlay.
    Displays detailed stats, genres, full overview, and trailers triggers.
    """
    movie = st.session_state.get("selected_movie_details")
    if not movie:
        return
        
    title = movie.get("title", "Unknown")
    overview = movie.get("overview", "No synopsis available.")
    backdrop_url = movie.get("backdrop_url", "")
    poster_url = movie.get("poster_url", "")
    if not poster_url or not isinstance(poster_url, str) or poster_url.lower().strip() in ["", "n/a", "null", "none", "please_enter_your_api_key_here"] or "placeholder" in poster_url.lower() or "no+poster" in poster_url.lower() or "not+found" in poster_url.lower():
        poster_url = "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
        
    rating = movie.get("rating", "N/A")
    runtime = format_runtime(movie.get("runtime", ""))
    release_date = movie.get("release_date", "N/A")
    year = release_date.split("-")[0] if "-" in release_date else release_date
    genres = movie.get("genres", [])
    trailer_url = movie.get("trailer_url", "https://www.youtube.com")
    
    st.markdown("### 🎬 Dynamic Movie Spotlight")
    
    # Styled Glass Panel container
    with st.container():
        st.markdown(f"""
            <div class="glass-panel" style="margin-bottom: 2rem;">
                <div style="display: flex; flex-wrap: wrap; gap: 24px;">
                    <div style="flex: 1 1 250px; max-width: 280px;">
                        <img src="{poster_url}" style="width:100%; border-radius:12px; box-shadow:0 15px 30px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.06);" />
                    </div>
                    <div style="flex: 2 2 400px; display: flex; flex-direction: column;">
                        <h2 style="font-family:'Montserrat', sans-serif; font-size: 2.4rem; margin:0 0 10px 0; font-weight:800; color:#ffffff;">{title}</h2>
                        <div style="display:flex; align-items:center; gap:16px; margin-bottom:18px; color:#b3b3b3; font-size:0.9rem;">
                            <span style="color:#ff4d4d; font-weight:800; font-size:1.15rem;">⭐ {rating}/10</span>
                            <span style="background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:4px;">{year}</span>
                            <span style="background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:4px;">⏱️ {runtime}</span>
                        </div>
                        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px;">
                            {" ".join([f'<span style="background:rgba(229,9,20,0.15); border:1px solid rgba(229,9,20,0.3); color:#ff4d4d; font-size:0.8rem; padding:4px 12px; border-radius:20px; font-weight:600;">{g}</span>' for g in genres])}
                        </div>
                        <p style="font-size:1rem; line-height:1.6; color:#e0e0e0; margin-bottom:20px;">{overview}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Action columns inside the spotlight
        cols = st.columns([2.5, 2.5, 2.5, 4.5])
        with cols[0]:
            has_trailer = trailer_url and "youtube" in trailer_url.lower()
            if has_trailer:
                if st.button("▶ Watch Trailer", key="spotlight_trailer_btn", use_container_width=True, type="primary"):
                    st.session_state.active_trailer_movie = movie
                    st.rerun()
            else:
                st.button("🚫 No Trailer", disabled=True, key="spotlight_notrailer_btn", use_container_width=True)
        with cols[1]:
            watchlist = st.session_state.setdefault("watchlist", [])
            is_in_wl = any(w["title"].lower() == title.lower() for w in watchlist)
            if is_in_wl:
                if st.button("❌ Remove List", key="spotlight_wl_btn", use_container_width=True, type="secondary"):
                    st.session_state.watchlist = [w for w in watchlist if w["title"].lower() != title.lower()]
                    st.toast(f"Removed '{title}' from watchlist!", icon="🗑️")
                    st.rerun()
            else:
                if st.button("💖 Add Watchlist", key="spotlight_wl_btn", use_container_width=True, type="secondary"):
                    st.session_state.watchlist.append(movie)
                    st.toast(f"Added '{title}' to watchlist!", icon="💖")
                    st.rerun()
        with cols[2]:
            if st.button("🎯 Find Similar", key="spotlight_sim_btn", use_container_width=True, type="secondary"):
                st.session_state.searched_movie = title
                st.session_state.recommendations = []
                st.session_state.active_page = "Recommend"
                st.rerun()
        with cols[3]:
            if st.button("✖ Close Spotlight", key="spotlight_close_btn", use_container_width=True, type="secondary"):
                st.session_state.selected_movie_details = None
                st.rerun()

def render_active_trailer_embed():
    """Renders a beautiful overlay modal block containing the streaming trailer."""
    movie = st.session_state.get("active_trailer_movie")
    if not movie:
        return
        
    title = movie.get("title", "Unknown")
    trailer_url = movie.get("trailer_url")
    
    st.markdown("---")
    st.markdown(f"### 🎬 Watching Trailer: **{title}**")
    
    # Custom bordered glass frame wrapper using st.container(border=True)
    with st.container(border=True):
        st.video(trailer_url)
        
        # Close triggers
        if st.button("✖ Close Video Player", key="close_trailer_player", use_container_width=True):
            st.session_state.active_trailer_movie = None
            st.rerun()
