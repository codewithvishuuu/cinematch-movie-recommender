import streamlit as st
import time
from omdb_api import get_popular_movies, fetch_movie_details
from recommender import get_all_movies, get_recommendations

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CineMatch | Movie Recommender",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "searched_movie" not in st.session_state:
    st.session_state.searched_movie = ""
if "popular_movies" not in st.session_state:
    st.session_state.popular_movies = []
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# --- CUSTOM CSS ---
def inject_custom_css():
    theme = st.session_state.get("theme", "dark")
    
    if theme == "dark":
        bg_color = "#12141a" # Dark bluish-grey base from screenshot
        text_color = "#ffffff"
        card_bg = "#161a20"
        border_color = "#242831"
        
        input_bg = "#1e222b"
        input_text = "#ffffff"
        input_border = "#333945"
        dropdown_bg = "#1e222b"
        sidebar_bg = "#1a1c23"
    else:
        bg_color = "#f6f7fb"
        text_color = "#111111"
        card_bg = "transparent"
        border_color = "#dddddd"
        
        input_bg = "#ffffff"
        input_text = "#000000"
        input_border = "#dddddd"
        dropdown_bg = "#ffffff"
        sidebar_bg = "#ffffff"

    # Hero gradient exactly matching the light sea-green one in the screenshot
    hero_gradient = "linear-gradient(135deg, #74b89e 0%, #a6dec9 100%)"
    
    # Red recommend button
    btn_bg = "#ff4b4b"
    btn_hover = "#ff3333"

    st.markdown(f"""
        <style>
        /* Global Backgrounds */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Typography overrides */
        h1, h2, h3, h4, h5, h6, p, span, label, div {{
            color: {text_color};
            font-family: 'Inter', sans-serif;
        }}

        /* Streamlit Input & Selectbox Styling Fixes */
        div[data-baseweb="select"] > div, 
        input, 
        textarea,
        .stSelectbox,
        .stTextInput {{
            background-color: {input_bg} !important;
            color: {input_text} !important;
            border: 1px solid {input_border} !important;
            -webkit-text-fill-color: {input_text} !important;
        }}
        
        /* Base overrides to handle dropdown portals injected at bottom of DOM */
        div[data-baseweb="menu"],
        div[data-baseweb="popover"] {{
            background-color: {dropdown_bg} !important;
        }}
        
        /* Target the actual popup portalled by Streamlit */
        div[data-baseweb="popover"] > div,
        div[role="listbox"],
        ul[role="listbox"], 
        li[role="option"] {{
            background-color: {dropdown_bg} !important;
            color: {input_text} !important;
        }}

        /* Fix Radio button text color since it's used for Theme toggle */
        div[role="radiogroup"] label {{
            color: {text_color} !important;
        }}
        div[role="radio"] div {{
            background-color: {input_bg} !important;
            border-color: {input_border} !important;
        }}

        /* Fix clear icon block */
        div[data-baseweb="select"] svg {{
            fill: {text_color} !important;
        }}

        /* Hero Banner matching the screenshot */
        .hero-banner {{
            background: {hero_gradient};
            padding: 2.5rem 2rem;
            border-radius: 12px;
            text-align: center;
            color: #ffffff !important;
            margin-bottom: 2.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        .hero-banner h1, .hero-banner p, .hero-banner span, .hero-banner div {{
            color: #ffffff !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.15);
        }}
        .hero-banner h1 {{
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .hero-banner p.description {{
            font-size: 1.2rem; 
            margin-bottom: 0;
            font-weight: 500;
        }}
        
        /* Movie Cards container styling using :has pseudo-class */
        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(15px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Making styling transparent since the layout requested matches native spacing but with smooth hover */
        div[data-testid="column"]:has(.movie-card-marker) {{
            background-color: transparent !important;
            padding: 8px !important;
            border: none !important;
            box-shadow: none !important;
            transition: transform 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            animation: fadeUp 0.6s ease-out forwards;
        }}
        
        div[data-testid="column"]:has(.movie-card-marker):hover {{
            transform: scale(1.04);
            z-index: 10;
        }}

        div[data-testid="column"]:has(.movie-card-marker) img {{
            border-radius: 8px !important;
            object-fit: cover !important;
            aspect-ratio: 2/3;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            margin-bottom: 12px;
        }}

        /* Card Texts exactly like screenshot layout */
        .movie-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin: 4px 0;
            text-align: center;
            color: {text_color} !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .movie-rating {{
            text-align: center;
            color: #f39c12 !important;
            font-weight: bold;
            font-size: 0.95rem;
            margin-bottom: 10px;
        }}
        
        .movie-overview {{
            font-size: 0.85rem;
            color: {text_color} !important;
            opacity: 0.7;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;  
            overflow: hidden;
            text-align: justify;
            line-height: 1.4;
        }}

        /* Recommend Button Styling (Red and rounded) */
        div[data-testid="stButton"] > button[kind="primary"] {{
            background-color: {btn_bg} !important;
            border: none;
            color: white !important;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1.1rem;
            padding: 0.6rem 2rem;
            transition: background-color 0.2s ease, transform 0.2s ease;
        }}
        div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background-color: {btn_hover} !important;
            transform: translateY(-2px);
        }}
        div[data-testid="stButton"] > button[kind="primary"] * {{
            color: white !important;
        }}

        /* Sidebar Spacing & Styling */
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
            border-right: 1px solid {border_color};
        }}
        
        /* Hide selectbox label */
        label[data-testid="stSelectboxLabel"] {{
            display: flex;
            margin-bottom: 8px;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- COMPONENTS ---
def render_movie_card(movie_data):
    """Renders a movie card utilizing Streamlit's native st.image combined with HTML markup below."""
    if not movie_data:
        return
        
    poster_url = movie_data.get('poster_url', '')
    if poster_url == "N/A" or not poster_url:
        poster_url = "https://via.placeholder.com/500x750?text=No+Poster"

    title = movie_data.get('title', 'Unknown')
    rating = movie_data.get('rating', 'N/A')
    overview = movie_data.get('overview', 'No overview available.')

    # Hidden marker to allow CSS to target this parent column layout
    st.markdown("<div class='movie-card-marker'></div>", unsafe_allow_html=True)
    
    # Native Streamlit Image component, taking full width of the column
    st.image(poster_url, use_container_width=True)
    
    # Texts below the image formatted like original layout
    st.markdown(f"""
        <div class="movie-title" title="{title}">{title}</div>
        <div class="movie-rating">⭐ {rating}/10</div>
        <div class="movie-overview">{overview}</div>
    """, unsafe_allow_html=True)

# --- PAGE ROUTING ---
def render_home_page():
    # Hero Section - Matching Screenshot
    st.markdown("""
        <div class="hero-banner">
            <h1>🍿 CineMatch</h1>
            <p class="description">Discover your next favorite movie with our intelligent content-based recommendation engine.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔥 Popular Movies")
    
    # Fetch popular movies only once per session
    if not st.session_state.popular_movies:
        with st.spinner("Fetching popular movies..."):
            st.session_state.popular_movies = get_popular_movies()
            time.sleep(0.5) # for UX
            
    popular = st.session_state.popular_movies
    
    if not popular:
        st.warning("Could not fetch popular movies. Please ensure your OMDb API Key is configured in the `.env` file.")
    else:
        # Display in a responsive grid - 6 columns as seen in screenshot
        cols_per_row = 6
        for i in range(0, len(popular), cols_per_row):
            cols = st.columns(cols_per_row, gap="medium")
            for j in range(cols_per_row):
                if i + j < len(popular):
                    with cols[j]:
                        render_movie_card(popular[i + j])

def render_recommend_page():
    # Matching screenshot exactly
    st.markdown("## 🎬 Find Movie Recommendations")
    st.write("Search for a movie you love, and we'll recommend similar titles based on genres, keywords, and storyline.")
    
    movie_list = get_all_movies()
    if not movie_list:
        st.error("Model data (pickle files) could not be loaded. Please ensure the pickle files exist in the project directory.")
        return
        
    selected_movie = st.selectbox(
        "📝 Type or select a movie:",
        options=[""] + movie_list,
        index=0
    )
    
    if st.button("Recommend", type="primary", use_container_width=True):
        if not selected_movie:
            st.warning("Please select a movie first!")
        else:
            st.session_state.searched_movie = selected_movie
            # Reset recommendations to trigger new fade-in
            st.session_state.recommendations = []
            
            with st.spinner(f"Generating recommendations for '{selected_movie}'..."):
                # Get titles
                rec_titles = get_recommendations(selected_movie, n_recommendations=5)
                
                if not rec_titles:
                    st.error("No recommendations found. This movie might not be in our database.")
                else:
                    # Fetch details for UI
                    detailed_recs = []
                    for title in rec_titles:
                        details = fetch_movie_details(title)
                        detailed_recs.append(details)
                    st.session_state.recommendations = detailed_recs

    st.markdown("---")
    
    # Display results if available
    if st.session_state.recommendations:
        st.markdown(f"### Next Picks for fans of {st.session_state.searched_movie}:")
        
        # 5 column layout for recommendations
        num_recs = len(st.session_state.recommendations)
        grid_cols = max(5, num_recs)
        
        cols = st.columns(grid_cols, gap="medium")
        for col, rec in zip(cols[:num_recs], st.session_state.recommendations):
            with col:
                render_movie_card(rec)

def render_about_page():
    st.title("💡 About CineMatch")
    
    st.markdown("""
    ### 🧠 How it Works
    CineMatch is a **Content-Based Filtering** recommendation system.
    It suggests movies similar to the one you search for based on:
    - **Genres**
    - **Keywords / Tags**
    - **Cast & Crew**
    - **Storyline Overview**
    
    We generate a **TF-IDF (Term Frequency-Inverse Document Frequency)** matrix from these textual details and compute the **Cosine Similarity** to find the closest matches.
    
    ### 🛠️ Technologies Used
    - **Python**: Core logic
    - **Streamlit**: Beautiful, responsive Frontend UI
    - **Scikit-Learn**: Machine Learning backend (TF-IDF & Cosine Similarity)
    - **Pandas**: Data manipulation
    - **OMDb API**: Fetching high-quality posters, ratings, and synopses.
    
    ### 👨‍💻 Developer
    Developed as an ML Project demonstrating end-to-end model deployment with an elegant user interface.
    """)

# --- MAIN APP EXECUTION ---
def main():
    inject_custom_css()
    
    # Sidebar Navigation & Settings
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3171/3171927.png", width=60) # Simple popcorn icon
        st.title("Menu")
        
        st.caption("Navigation")
        page = st.radio("Navigation", ["Home", "Recommend", "About"], label_visibility="collapsed")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 🎨 Theme")
        
        # Theme Toggle
        theme_index = 0 if st.session_state.theme == "dark" else 1
        selected_theme = st.radio("Appearance", ["Dark", "Light"], index=theme_index, horizontal=True, label_visibility="collapsed")
        
        if selected_theme.lower() != st.session_state.theme:
            st.session_state.theme = selected_theme.lower()
            st.rerun()
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.caption("Powered by OMDb API & Scikit-learn")
        
    # Render Selected Page
    if page == "Home":
        render_home_page()
    elif page == "Recommend":
        render_recommend_page()
    elif page == "About":
        render_about_page()

if __name__ == "__main__":
    main()
