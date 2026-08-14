import html
import streamlit as st
from components.ui import format_runtime


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


def render_movie_hero(movie):
    """
    Renders the cinematic hero spotlight: kicker badge, title, metadata pills,
    overview, cast and action buttons. Backdrop zoom + content fade on load.
    """
    if not movie:
        return

    title_raw = movie.get("title", "Unknown")
    title = _esc(title_raw)
    overview = _esc(movie.get("overview", "No description available."))

    # Backdrop validation (honest fallback only when missing)
    backdrop_url = movie.get("backdrop_url", "")
    if not backdrop_url or not isinstance(backdrop_url, str) or backdrop_url.lower().strip() in ["", "n/a", "null", "none"]:
        backdrop_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1280&auto=format&fit=crop"

    rating = _rating_str(movie.get("rating"))
    runtime = format_runtime(movie.get("runtime", ""))
    release_date = movie.get("release_date", "N/A")
    year = release_date.split("-")[0] if "-" in release_date else (release_date or "N/A")

    genres = movie.get("genres", []) or []
    genre_tags = " · ".join(_esc(g) for g in genres)

    cast = movie.get("cast", []) or []
    cast_html = ""
    if cast:
        cast_names = ", ".join(_esc(c) for c in cast[:4])
        cast_html = (
            '<div class="cm-hero-cast">'
            '<span class="cm-cast-label">Starring</span>'
            f'<span class="cm-cast-names">{cast_names}</span>'
            '</div>'
        )

    meta_html = (
        f'<span class="cm-meta-pill">{year}</span>'
        f'<span class="cm-meta-pill cm-meta-rating">★ {rating} / 10</span>'
        f'<span class="cm-meta-pill">⏱ {runtime}</span>'
        + (f'<span class="cm-meta-genres">{genre_tags}</span>' if genre_tags else "")
    )

    hero_html = (
        '<div class="cm-hero">'
        f'<div class="cm-hero-backdrop" style="background-image: url(\'{backdrop_url}\');"></div>'
        '<div class="cm-hero-scrim"></div>'
        '<div class="cm-hero-content">'
        '<div class="cm-hero-kicker"><span class="cm-kicker-dot"></span><span>Featured Blockbuster</span></div>'
        f'<h1 class="cm-hero-title">{title}</h1>'
        f'<div class="cm-hero-meta">{meta_html}</div>'
        f'<p class="cm-hero-overview">{overview}</p>'
        f'{cast_html}'
        '</div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # Interactive action row (marker-scoped for the premium hero button sizing)
    has_trailer = movie.get("trailer_url") and "youtube.com/watch" in movie.get("trailer_url").lower()
    title_key = title_raw.replace(" ", "_")

    cols = st.columns([2.2, 2.8, 7.0], gap="small")
    with cols[0]:
        st.markdown('<div class="cm-hero-actions-marker"></div>', unsafe_allow_html=True)
        if has_trailer:
            if st.button("▶ WATCH TRAILER", key=f"hero_play_mod_{title_key}", width="stretch", type="primary"):
                st.session_state.active_trailer_movie = movie
                st.rerun()
        else:
            st.button("▶ NO TRAILER", key=f"hero_no_play_mod_{title_key}", width="stretch", disabled=True)

    with cols[1]:
        watchlist = st.session_state.setdefault("watchlist", [])
        is_in_wl = any(w.get("title", "").lower() == title_raw.lower() for w in watchlist)

        if is_in_wl:
            if st.button("✓ REMOVE FROM LIST", key=f"hero_wl_rem_mod_{title_key}", width="stretch", type="secondary"):
                st.session_state.watchlist = [w for w in watchlist if w.get("title", "").lower() != title_raw.lower()]
                st.toast(f"Removed '{title_raw}' from watchlist!", icon="🗑️")
                st.rerun()
        else:
            if st.button("＋ ADD TO WATCHLIST", key=f"hero_wl_add_mod_{title_key}", width="stretch", type="secondary"):
                st.session_state.watchlist.append(movie)
                st.toast(f"Added '{title_raw}' to watchlist!", icon="💖")
                st.rerun()