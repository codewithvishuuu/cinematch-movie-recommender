import streamlit as st
from components.ui import render_movie_card, render_details_overlay_panel, render_active_trailer_embed

def render_watchlist_view():
    """Renders the user's customized Watchlist page."""
    st.markdown("""
        <h1 class="cm-page-title">Your Watchlist</h1>
        <p class="cm-page-sub">
            Keep track of the masterpieces you want to experience next. Click details to watch trailers or find matching stories.
        </p>
    """, unsafe_allow_html=True)
    
    # 1. Overlay Drawers
    if st.session_state.get("active_trailer_movie"):
        render_active_trailer_embed()
        st.markdown("---")
        
    if st.session_state.get("selected_movie_details"):
        render_details_overlay_panel()
        st.markdown("---")
        
    # 2. Get list of movies in watchlist
    watchlist = st.session_state.setdefault("watchlist", [])
    
    if not watchlist:
        # Beautiful visual empty state
        st.markdown("""
            <div class="cm-empty">
                <div style="font-size: 4rem; margin-bottom: 1.2rem;">🍿</div>
                <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.4rem; color: #ffffff;">Your Watchlist is Empty</h3>
                <p style="color: #a6a6b2; max-width: 520px; margin: 0 auto 2rem auto; font-size: 0.95rem; line-height: 1.65;">
                    Explore trending content on the Home tab or configure intelligent story filters to discover matching titles, then click "+ List" to save them here!
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Call to action button to jump directly to recommender
        cols = st.columns([4, 4, 4])
        with cols[1]:
            if st.button("FIND MOVIES TO SAVE", width="stretch", type="primary"):
                st.session_state.active_page = "Recommend"
                st.rerun()
                
    else:
        # Clear Watchlist option
        col_title, col_clear = st.columns([8, 4])
        with col_clear:
            if st.button("CLEAR ENTIRE WATCHLIST", width="stretch", type="secondary"):
                st.session_state.watchlist = []
                st.toast("Cleared watchlist successfully!", icon="🗑️")
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Render Watchlist Grid
        cols_per_row = 6
        for i in range(0, len(watchlist), cols_per_row):
            cols = st.columns(cols_per_row, gap="medium")
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(watchlist):
                    with cols[j]:
                        render_movie_card(watchlist[idx], key_prefix=f"wl_{idx}")
            st.markdown("<br>", unsafe_allow_html=True)
