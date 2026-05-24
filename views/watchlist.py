import streamlit as st
from components.ui import render_movie_card, render_details_overlay_panel, render_active_trailer_embed

def render_watchlist_view():
    """Renders the user's customized Watchlist page."""
    st.markdown("""
        <div class="section-title-container" style="margin-top: 1rem;">
            <h1 style="margin: 0; font-size: 2.2rem;">💖 Your Watchlist</h1>
        </div>
        <p style="color: #b3b3b3; font-size: 1.1rem; margin-bottom: 2rem;">
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
            <div style="text-align: center; padding: 4rem 2rem; background: rgba(255,255,255,0.02); border-radius: 16px; border: 1px dashed rgba(229, 9, 20, 0.3);">
                <div style="font-size: 4.5rem; margin-bottom: 1.5rem;">🍿</div>
                <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.5rem; color: #ffffff;">Your Watchlist is Empty</h3>
                <p style="color: #b3b3b3; max-width: 500px; margin: 0 auto 2rem auto; font-size: 1rem; line-height: 1.6;">
                    Explore trending content on the Home tab or configure intelligent story filters to discover matching titles, then click "+ List" to save them here!
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Call to action button to jump directly to recommender
        cols = st.columns([4, 4, 4])
        with cols[1]:
            if st.button("🔍 Find Movies to Save", use_container_width=True):
                st.session_state.active_page = "Recommend"
                st.rerun()
                
    else:
        # Clear Watchlist option
        col_title, col_clear = st.columns([8, 4])
        with col_clear:
            if st.button("🗑️ Clear Entire Watchlist", use_container_width=True):
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
