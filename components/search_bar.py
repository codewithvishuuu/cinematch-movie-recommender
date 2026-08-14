import streamlit as st
from services.search_service import search_movies_pipeline

def render_search_bar():
    """
    Renders an elite, glassmorphic cinematic search deck at the top of the Home view.
    Includes debounced text inputs, instant submit triggers, and quick suggestion chips.
    """
    st.markdown("""
        <div class="cm-panel cm-panel-accent" style="margin-top: 1rem; margin-bottom: 1.5rem; padding: 22px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                <span style="font-size: 1.6rem;">🔍</span>
                <h3 class="cm-panel-title" style="margin-bottom: 0;">Discover Cinematic Masterpieces</h3>
            </div>
            <p style="color:#a6a6b2; font-size:0.9rem; margin:0 0 15px 0; line-height: 1.55;">
                Type any movie title. Our smart typo-correcting pipeline queries both our local 42,141-title AI database and TMDB live to compile instant recommendations.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Autocomplete Search Input
    c_input, c_btn = st.columns([8.5, 1.5], gap="small")
    
    # Initialize search state
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
        
    with c_input:
        search_val = st.text_input(
            "Search Movie",
            value=st.session_state.search_query,
            placeholder="Type 'toystory', 'dark knight', 'avengers', 'interstellar'...",
            label_visibility="collapsed",
            key="search_input_widget"
        )
        
    with c_btn:
        search_clicked = st.button("Search", key="search_submit_btn", width="stretch")

    # Sync search widget with state
    if search_val != st.session_state.search_query or search_clicked:
        st.session_state.search_query = search_val
        if search_val.strip():
            # Trigger pipeline immediately and cache recommendations in session
            with st.spinner("Decoding storyline indices..."):
                results = search_movies_pipeline(search_val)
                st.session_state.autocomplete_results = results
                # Auto-select the first match as our main search spotlight to prevent empty search state
                if results:
                    st.session_state.matched_search_movie = results[0]
        else:
            st.session_state.autocomplete_results = []
            st.session_state.matched_search_movie = None
            
    # 2. Rendering Quick Suggestion Chips in a clean, spacious 2x5 grid layout
    st.markdown("<div style='margin-top: 15px; margin-bottom: 8px; font-size: 0.78rem; color: #63636e; font-weight: 700; letter-spacing: 1.6px;'>TRENDING SUGGESTIONS</div>", unsafe_allow_html=True)
    
    chips = ["Interstellar", "Inception", "The Dark Knight", "The Avengers", "Toy Story", "Heat", "Gladiator", "Avatar", "Deadpool", "Guardians"]
    
    # Split into 2 rows of 5 columns
    chips_r1 = chips[:5]
    chips_r2 = chips[5:]
    
    def render_chip_row(chip_list, prefix):
        cols = st.columns(5)
        for idx, chip in enumerate(chip_list):
            with cols[idx]:
                if st.button(chip, key=f"chip_{prefix}_{idx}", width="stretch", type="secondary"):
                    st.session_state.search_query = chip
                    # Instantly compute recommendations and spotlight
                    with st.spinner(f"Spotlighting '{chip}'..."):
                        from services.tmdb_service import fetch_movie_details
                        details = fetch_movie_details(chip)
                        if details:
                            st.session_state.selected_movie_details = details
                            st.session_state.searched_movie = chip
                            st.session_state.hero_movie = details
                            # Force recommendations load
                            from ml.recommender import get_recommendations
                            rec_items = get_recommendations(chip, n_recommendations=10)
                            detailed_recs = []
                            for item in rec_items:
                                det = fetch_movie_details(item["title"])
                                if det:
                                    det["relevance_score"] = item["relevance_score"]
                                    det["match_reason"] = item["reason"]
                                    det["match_label"] = item.get("match_label")
                                    det["match_score"] = item.get("match_score")
                                    detailed_recs.append(det)
                            st.session_state.recommendations = detailed_recs
                            st.session_state.autocomplete_results = []
                            st.session_state.search_query = ""
                            st.toast(f"Active spotlight set to '{chip}'!", icon="🍿")
                            st.rerun()

    render_chip_row(chips_r1, "row1")
    st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)
    render_chip_row(chips_r2, "row2")
