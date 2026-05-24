import streamlit as st
from services.tmdb_service import fetch_movie_details
from ml.recommender import get_recommendations

def render_autocomplete_dropdown():
    """
    Renders an immersive autocomplete suggestions overlay panel.
    Displays search results with live poster thumbnails, rating badges, years, and genre tags.
    Clicking a suggestion immediately sets it as active spotlight and triggers recommender calculations.
    """
    results = st.session_state.get("autocomplete_results", [])
    if not results:
        return
        
    st.markdown("""
        <div class="section-title-container" style="margin-top: 1rem; margin-bottom: 0.8rem;">
            <h4 style="margin: 0; font-size: 1.1rem; color: #ff4d4d; font-family:'Montserrat',sans-serif; text-transform: uppercase; letter-spacing:1px;">✨ Live Matches Found</h4>
        </div>
    """, unsafe_allow_html=True)
    
    # Outer Glass Panel Container for autocomplete list using st.container(border=True)
    with st.container(border=True):
        for idx, movie in enumerate(results[:5]):
            title = movie.get("title", "Unknown")
            poster_url = movie.get("poster_url", "")
            if not poster_url or not isinstance(poster_url, str) or "placeholder" in poster_url.lower() or "no+poster" in poster_url.lower():
                poster_url = "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop"
                
            rating = movie.get("rating", "7.0")
            release_date = movie.get("release_date", "N/A")
            year = release_date.split("-")[0] if "-" in release_date else release_date
            genres = movie.get("genres", ["Feature"])
            genres_joined = " • ".join(genres)
            
            # Horizontal suggestion card layout
            c_thumb, c_info, c_action = st.columns([1.2, 7.3, 1.5], gap="small")
            
            with c_thumb:
                st.image(poster_url, use_container_width=True)
                
            with c_info:
                st.markdown(f"""
                    <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                        <h4 style="margin: 0 0 4px 0; font-size: 1.15rem; font-family:'Montserrat',sans-serif; font-weight:800; color: #ffffff;">{title}</h4>
                        <div style="display: flex; align-items: center; gap: 12px; font-size: 0.82rem; color: #b3b3b3;">
                            <span style="color: #ff4d4d; font-weight: 800;">⭐ {rating}</span>
                            <span style="background: rgba(255,255,255,0.06); padding: 1px 6px; border-radius: 4px;">{year}</span>
                            <span style="color: #8c8c8c;">|  {genres_joined}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            with c_action:
                # Click action button
                if st.button("Select", key=f"select_dropdown_{idx}_{title.replace(' ', '_')}", use_container_width=True):
                    with st.spinner(f"Spotlighting '{title}'..."):
                        # Get complete details
                        details = fetch_movie_details(title)
                        if details:
                            st.session_state.selected_movie_details = details
                            st.session_state.searched_movie = title
                            st.session_state.hero_movie = details
                            
                            # Trigger recommendations calculations immediately
                            rec_items = get_recommendations(title, n_recommendations=10)
                            detailed_recs = []
                            for item in rec_items:
                                det = fetch_movie_details(item["title"])
                                if det:
                                    det["relevance_score"] = item["relevance_score"]
                                    det["match_reason"] = item["reason"]
                                    detailed_recs.append(det)
                            st.session_state.recommendations = detailed_recs
                            
                            # Reset query to close autocomplete suggestion deck
                            st.session_state.autocomplete_results = []
                            st.session_state.search_query = ""
                            st.toast(f"Active spotlight set to '{title}'!", icon="🍿")
                            st.rerun()
                
            st.markdown("<hr style='border-color: rgba(255, 255, 255, 0.05); margin: 8px 0;'>", unsafe_allow_html=True)
            
        # Standard Close button inside the dropdown panel
        c_close_l, c_close_r = st.columns([8.5, 1.5])
        with c_close_r:
            if st.button("Close Panel", key="close_dropdown_overlay_btn", use_container_width=True, type="secondary"):
                st.session_state.autocomplete_results = []
                st.session_state.search_query = ""
                st.rerun()
