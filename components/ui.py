import html
import logging
import os
import streamlit as st
from services.tmdb_service import fetch_movie_details

# Base path for main.css
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger("cinematch.ui")


def _esc(value):
    """Escapes a value for safe HTML interpolation (titles/overviews from TMDB)."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _rating_str(rating):
    """Displays a rating honestly: real value, or '—' when unavailable."""
    if rating is None:
        return "—"
    try:
        return str(round(float(rating), 1))
    except (TypeError, ValueError):
        return "—"


def inject_netflix_theme():
    """Injects the CineMatch cinematic UI stylesheet into the viewport."""
    css_path = os.path.join(BASE_DIR, 'assets', 'main.css')
    try:
        with open(css_path, 'r') as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning("Error loading main.css: %s", e)
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
    except (TypeError, ValueError):
        return f"{minutes} mins"


def _valid_backdrop(movie):
    """Validates and returns a backdrop URL (honest fallback only when missing)."""
    backdrop_url = movie.get("backdrop_url", "")
    if not backdrop_url or not isinstance(backdrop_url, str) or backdrop_url.lower().strip() in ["", "n/a", "null", "none"]:
        return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1280&auto=format&fit=crop"
    return backdrop_url


def _valid_poster(movie):
    """Validates and returns a poster URL (honest fallback only when missing)."""
    poster_url = movie.get("poster_url", "")
    if not poster_url or not isinstance(poster_url, str):
        return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
    stripped = poster_url.strip().lower()
    if stripped in ["", "n/a", "null", "none", "null.jpg", "not found", "na"]:
        return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
    if any(marker in stripped for marker in ("placeholder", "no+poster", "no_poster", "notfound", "not+found")):
        return "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
    return poster_url


def _movie_year(movie):
    """Extracts a display year from a movie dict's release date."""
    release_date = movie.get("release_date", "N/A")
    if "-" in release_date:
        return release_date.split("-")[0]
    return release_date or "N/A"


def render_section_header(title, subtitle=None):
    """Renders a cinematic section heading with accent line and optional subtitle."""
    sub_html = f'<p class="cm-section-sub">{_esc(subtitle)}</p>' if subtitle else ""
    st.markdown(
        '<div class="cm-section-head">'
        '<div class="cm-section-accent"></div>'
        f'<h2 class="cm-section-title">{_esc(title)}</h2>'
        f'{sub_html}'
        '</div>',
        unsafe_allow_html=True,
    )


def render_skeleton_cards(count=6):
    """Renders shimmer placeholder cards in a grid matching the real card layout."""
    cols = st.columns(count, gap="medium")
    for col in cols:
        with col:
            st.markdown(
                '<div class="cm-skeleton">'
                '<div class="cm-sk-poster"></div>'
                '<div class="cm-sk-body">'
                '<div class="cm-sk-line cm-sk-w70"></div>'
                '<div class="cm-sk-line cm-sk-w45"></div>'
                '<div class="cm-sk-line cm-sk-w90"></div>'
                '</div>'
                '<div class="cm-sk-actions"><span></span><span></span><span></span></div>'
                '</div>',
                unsafe_allow_html=True,
            )


def render_hero_section(movie):
    """Compatibility alias - renders the premium hero (shared implementation)."""
    from components.movie_hero import render_movie_hero
    render_movie_hero(movie)


def render_movie_card(movie, key_prefix="card", relevance_score=None, match_reason=None, match_label=None):
    """
    Renders a premium movie card: poster, title, meta, overview, AI insight,
    and an INFO / PLAY / ADD action row (labels never wrap).
    """
    if not movie:
        return

    title_raw = movie.get("title", "Unknown")
    title = _esc(title_raw)
    poster_url = _valid_poster(movie)
    rating = _rating_str(movie.get("rating"))
    year = _movie_year(movie)
    genres = movie.get("genres", []) or []
    overview = _esc(movie.get("overview", "No synopsis available."))

    # Calibrated match label (unchanged semantics: label, score fallback, generic).
    if match_label:
        badge_text = _esc(str(match_label).upper())
    elif relevance_score is not None:
        badge_text = "MATCHED"
    else:
        badge_text = "POPULAR"

    genre_row = " · ".join(_esc(g) for g in genres[:3])
    meta_row = (
        f'<span class="cm-card-rating">★ {rating}</span>'
        f'<span class="cm-card-dot">·</span>'
        f'<span class="cm-card-year">{year}</span>'
        + (f'<span class="cm-card-dot">·</span><span class="cm-card-genres">{genre_row}</span>' if genre_row else "")
    )

    card_html = (
        '<div class="movie-card-marker"></div>'
        '<div class="cm-movie-card">'
        '<div class="cm-poster-frame">'
        f'<img src="{poster_url}" alt="{title}" loading="lazy" decoding="async" />'
        '<div class="cm-poster-shade"></div>'
        f'<span class="cm-card-badge">{badge_text}</span>'
        '</div>'
        '<div class="cm-card-body">'
        f'<div class="cm-card-title" title="{title}">{title}</div>'
        f'<div class="cm-card-meta">{meta_row}</div>'
        f'<div class="cm-card-overview">{overview}</div>'
        '</div>'
        '</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # AI explanation panel if present
    if match_reason:
        st.markdown(
            f'<div class="ai-reason-banner"><span class="ai-reason-tag">AI INSIGHT</span> {_esc(match_reason)}</div>',
            unsafe_allow_html=True,
        )

    # Action row: INFO | PLAY | ADD — equal heights, never-wrapping labels
    has_trailer = movie.get("trailer_url") and "youtube.com/watch" in movie.get("trailer_url").lower()
    watchlist = st.session_state.setdefault("watchlist", [])
    is_in_wl = any(w.get("title", "").lower() == title_raw.lower() for w in watchlist)

    c1, c2, c3 = st.columns(3, gap="small")

    with c1:
        if st.button("ⓘ INFO", key=f"{key_prefix}_details_{title_raw}", width="stretch",
                     help="Open the full detail spotlight"):
            st.session_state.selected_movie_details = movie
            st.rerun()

    with c2:
        if has_trailer:
            if st.button("▶ PLAY", key=f"{key_prefix}_play_{title_raw}", width="stretch",
                         help="Watch the official trailer"):
                st.session_state.active_trailer_movie = movie
                st.rerun()
        else:
            st.button("▶ PLAY", key=f"{key_prefix}_noplay_{title_raw}", width="stretch",
                      disabled=True, help="No trailer available for this title")

    with c3:
        if is_in_wl:
            if st.button("✓ SAVED", key=f"{key_prefix}_wl_{title_raw}", width="stretch",
                         help="Remove from watchlist"):
                st.session_state.watchlist = [w for w in watchlist if w.get("title", "").lower() != title_raw.lower()]
                st.toast(f"Removed '{title_raw}' from watchlist!", icon="🗑️")
                st.rerun()
        else:
            if st.button("＋ ADD", key=f"{key_prefix}_wl_{title_raw}", width="stretch",
                         help="Add to watchlist"):
                st.session_state.watchlist.append(movie)
                st.toast(f"Added '{title_raw}' to watchlist!", icon="💖")
                st.rerun()


def render_details_overlay_panel():
    """
    Renders the cinematic detail spotlight panel with stats, genres, overview
    and trailer / watchlist / similar / close actions. Behavior unchanged.
    """
    movie = st.session_state.get("selected_movie_details")
    if not movie:
        return

    title_raw = movie.get("title", "Unknown")
    title = _esc(title_raw)
    overview = _esc(movie.get("overview", "No synopsis available."))
    backdrop_url = _valid_backdrop(movie)
    poster_url = _valid_poster(movie)

    rating = _rating_str(movie.get("rating"))
    runtime = format_runtime(movie.get("runtime", ""))
    year = _movie_year(movie)
    genres = movie.get("genres", []) or []
    trailer_url = movie.get("trailer_url")

    st.markdown('<div class="cm-spotlight-title">Movie Spotlight</div>', unsafe_allow_html=True)

    with st.container():
        genre_spans = " ".join(
            f'<span class="cm-genre-pill">{_esc(g)}</span>'
            for g in genres
        )
        st.markdown(
            '<div class="cm-panel" style="margin-bottom: 1.6rem;">'
            '<div style="display: flex; flex-wrap: wrap; gap: 24px;">'
            '<div style="flex: 1 1 240px; max-width: 280px;">'
            f'<img class="cm-spotlight-poster" src="{poster_url}" alt="{title}" />'
            '</div>'
            '<div style="flex: 2 2 420px; display: flex; flex-direction: column; min-width: 0;">'
            f'<h2 class="cm-hero-title" style="font-size: 2.1rem !important; margin-bottom: 0.8rem !important;">{title}</h2>'
            '<div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 16px;">'
            f'<span class="cm-meta-pill cm-meta-rating">★ {rating} / 10</span>'
            f'<span class="cm-meta-pill">{year}</span>'
            f'<span class="cm-meta-pill">⏱ {runtime}</span>'
            '</div>'
            f'<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px;">{genre_spans}</div>'
            f'<p style="font-size: 0.95rem; line-height: 1.65; color: #c9c9d4; margin: 0;">{overview}</p>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Action columns inside the spotlight
        has_trailer = trailer_url and "youtube.com/watch" in trailer_url.lower()
        watchlist = st.session_state.setdefault("watchlist", [])
        is_in_wl = any(w.get("title", "").lower() == title_raw.lower() for w in watchlist)

        cols = st.columns([2.2, 2.6, 2.2, 3.0])
        with cols[0]:
            if has_trailer:
                if st.button("▶ WATCH TRAILER", key="spotlight_trailer_btn", width="stretch", type="primary"):
                    st.session_state.active_trailer_movie = movie
                    st.rerun()
            else:
                st.button("▶ NO TRAILER", key="spotlight_notrailer_btn", width="stretch", disabled=True)
        with cols[1]:
            if is_in_wl:
                if st.button("✓ REMOVE FROM LIST", key="spotlight_wl_btn", width="stretch", type="secondary"):
                    st.session_state.watchlist = [w for w in watchlist if w.get("title", "").lower() != title_raw.lower()]
                    st.toast(f"Removed '{title_raw}' from watchlist!", icon="🗑️")
                    st.rerun()
            else:
                if st.button("＋ ADD TO WATCHLIST", key="spotlight_wl_btn", width="stretch", type="secondary"):
                    st.session_state.watchlist.append(movie)
                    st.toast(f"Added '{title_raw}' to watchlist!", icon="💖")
                    st.rerun()
        with cols[2]:
            if st.button("🎯 FIND SIMILAR", key="spotlight_sim_btn", width="stretch", type="secondary"):
                st.session_state.searched_movie = title_raw
                st.session_state.recommendations = []
                st.session_state.active_page = "Recommend"
                st.rerun()
        with cols[3]:
            if st.button("✕ CLOSE SPOTLIGHT", key="spotlight_close_btn", width="stretch", type="secondary"):
                st.session_state.selected_movie_details = None
                st.rerun()


def render_active_trailer_embed():
    """Renders the streaming trailer overlay block. Behavior unchanged."""
    movie = st.session_state.get("active_trailer_movie")
    if not movie:
        return

    title = _esc(movie.get("title", "Unknown"))
    trailer_url = movie.get("trailer_url")

    if not trailer_url or "youtube.com/watch" not in trailer_url.lower():
        # Trailer state should never point at a bare domain - guard defensively.
        st.session_state.active_trailer_movie = None
        return

    st.markdown("---")
    st.markdown(f"<div class='cm-spotlight-title'>Now Playing — {title}</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.video(trailer_url)

        if st.button("✕ CLOSE VIDEO PLAYER", key="close_trailer_player", width="stretch", type="secondary"):
            st.session_state.active_trailer_movie = None
            st.rerun()