import html
import streamlit as st
from ml.recommender import get_all_genres, get_recommendations
from services.tmdb_service import fetch_movie_details
from components.ui import render_movie_card, render_details_overlay_panel, render_active_trailer_embed, render_section_header
from components.search_bar import render_search_bar
from components.autocomplete_dropdown import render_autocomplete_dropdown
from components.movie_hero import render_movie_hero

# Premium Mood Emojis & Titles Map to Backend Keys
MOOD_BTN_MAP = {
    "😊 Feel Good": "Uplifting / Feel-Good",
    "🤯 Mind Bending": "Intense / Mind-Bending",
    "😱 Horror": "Spooky / Terrifying",
    "🔥 Action": "Thrilling / Action-Packed",
    "💔 Emotional": "Emotional / Melancholic",
    "🚀 Sci-Fi": "Thought-Provoking",
    "🧠 Thought Provoking": "Thought-Provoking"
}

def render_recommend_view():
    """Renders the advanced premium AI movie matching lab view."""
    st.markdown("""
        <h1 class="cm-page-title">AI Movie Intelligence Lab</h1>
        <p class="cm-page-sub">
            Discover films mathematically matched using storyline vectors. Search dynamically, apply mood overrides, and tweak semantic weights.
        </p>
    """, unsafe_allow_html=True)
    
    # 1. Advanced Real-time Search Panel (Exclusive to AI Master Lab)
    render_search_bar()
    render_autocomplete_dropdown()
    
    # 2. Overlay Drawers
    if st.session_state.get("active_trailer_movie"):
        render_active_trailer_embed()
        st.markdown("---")
        
    if st.session_state.get("selected_movie_details"):
        render_details_overlay_panel()
        st.markdown("---")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. 2-column parameter container
    c_left, c_right = st.columns([5.5, 6.5], gap="large")
    
    with c_left:
        st.markdown("""
            <div class="cm-panel cm-panel-accent" style="margin-bottom: 20px;">
                <h3 class="cm-panel-title">AI Parameter Deck</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Display selected movie spotlight status
        active_search = st.session_state.get("searched_movie", "")
        if active_search:
            st.markdown(f"""
                <div class="cm-banner cm-banner-ok">
                    Active Reference: {html.escape(str(active_search))}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="cm-banner cm-banner-warn">
                    No active movie selected. Search above or use the suggestion chips to begin.
                </div>
            """, unsafe_allow_html=True)
            
        # Multi-select genres filter
        genres = get_all_genres()
        selected_genres = st.multiselect(
            "🎬 Restrict to Genres (Optional):",
            options=genres,
            help="Limits matching results strictly to these movie genres."
        )
        
        # Glowing Mood buttons grid (4 columns layout for 7 buttons)
        st.markdown("🎭 **Select Psychological Mood Override (Soft Weight Boost):**")
        selected_mood_label = st.session_state.setdefault("selected_mood_label", "None")
        
        mood_cols = st.columns(4, gap="small")
        mood_keys = list(MOOD_BTN_MAP.keys())
        
        for idx, label in enumerate(mood_keys):
            col_idx = idx % 4
            with mood_cols[col_idx]:
                is_active = selected_mood_label == label
                btn_type = "primary" if is_active else "secondary"
                
                if st.button(label, key=f"mood_btn_{idx}", type=btn_type, width="stretch"):
                    selected_mood_label = "None" if is_active else label
                    st.session_state.selected_mood_label = selected_mood_label
                    st.rerun()
                    
        # Limit count slider
        rec_count = st.slider("📊 Sugestion Limit Range:", min_value=5, max_value=20, value=10, step=5)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Central action trigger
        if st.button("🚀 Calculate Cosine Similarities", type="primary", width="stretch"):
            if not active_search:
                st.warning("⚠️ Please search or click a quick suggestion trend chip first!")
            else:
                with st.spinner(f"Vectorizing storyline paths..."):
                    backend_mood = None
                    if selected_mood_label != "None":
                        backend_mood = MOOD_BTN_MAP[selected_mood_label]
                        
                    # Recommender generates rich dict results containing title, relevance_score, and reason
                    rec_items = get_recommendations(
                        active_search,
                        n_recommendations=rec_count,
                        genre_filter=selected_genres,
                        mood_filter=backend_mood
                    )
                    
                    if not rec_items:
                        st.error("😞 No recommendations matched this filter combination. Try adjusting parameters.")
                        st.session_state.recommendations = []
                    else:
                        detailed_recs = []
                        for item in rec_items:
                            details = fetch_movie_details(item["title"])
                            if details:
                                details["relevance_score"] = item["relevance_score"]
                                details["match_reason"] = item["reason"]
                                details["match_label"] = item.get("match_label")
                                details["match_score"] = item.get("match_score")
                                detailed_recs.append(details)
                        st.session_state.recommendations = detailed_recs
                        st.toast(f"AI Lab computed {len(detailed_recs)} similarity vector suggestions!", icon="🧬")
                        st.rerun()

    with c_right:
        st.markdown("""
            <div class="cm-panel">
                <h3 class="cm-panel-title">AI Pipeline Architecture</h3>
                <p style="color: #b3b3b3; line-height: 1.7; font-size: 0.95rem;">
                    The Laboratory maps storylines using high-dimensional cosine angle spaces on 42,141 canonical records. Precomputed TF-IDF sparse token matrices allow instant evaluation.
                </p>
                <h4 style="color:#ffffff; margin-bottom:10px;">🧬 How to operate:</h4>
                <ul style="color:#b3b3b3; line-height: 1.7; font-size:0.92rem; padding-left:20px;">
                    <li><b>Search Step:</b> Use the top autocomplete search input to query films.</li>
                    <li><b>Parameter Refinement:</b> Select specific genre exclusions or psychological mood overrides to alter rankings.</li>
                    <li><b>Hybrid Reranking:</b> We combine storyline content similarity, canonical genre overlap, a mean-centered quality rating signal and a small popularity signal to rank story-similar candidates. TMDB is only used to enrich posters, trailers and details — never for recommendation scoring.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # 4. Immersive selected movie spotlight hero panel + Recommendations Grid
    if active_search and st.session_state.get("selected_movie_details"):
        render_section_header("Reference Spotlight", f"Your story reference — {active_search}")
        render_movie_hero(st.session_state.selected_movie_details)
        st.markdown("<br>", unsafe_allow_html=True)
        
    if st.session_state.get("recommendations"):
        render_section_header(
            f"Vector Recommendations for \"{html.escape(str(active_search))}\"",
            f"Top {len(st.session_state.recommendations)} story-similar titles, ranked by cosine similarity."
        )
        
        recs = st.session_state.recommendations
        
        # Display recommendations in responsive rows of 5 columns
        cols_per_row = 5
        for i in range(0, len(recs), cols_per_row):
            cols = st.columns(cols_per_row, gap="medium")
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(recs):
                    item = recs[idx]
                    with cols[j]:
                        render_movie_card(
                            item, 
                            key_prefix=f"rec_lab_{idx}", 
                            relevance_score=item.get("relevance_score"),
                            match_reason=item.get("match_reason"),
                            match_label=item.get("match_label")
                        )
            st.markdown("<br>", unsafe_allow_html=True)
            
    elif active_search:
        st.info("💡 Click 'Calculate Cosine Similarities' to compile recommendations for your target movie.")
    else:
        st.info("🍿 Start by typing a movie title in the search input above, or select one of the trending suggestions chips!")
