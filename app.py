import streamlit as st
from config.settings import is_api_key_configured
from components.ui import inject_netflix_theme
from views.home import render_home_view
from views.recommend import render_recommend_view
from views.watchlist import render_watchlist_view
from views.about import render_about_view

# 1. Page Configuration (Must be first call)
st.set_page_config(
    page_title="CineMatch | Premium AI Movie Discovery Engine",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. State Initialization
def init_session_states():
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Home"
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    if "searched_movie" not in st.session_state:
        st.session_state.searched_movie = ""
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []
    if "selected_movie_details" not in st.session_state:
        st.session_state.selected_movie_details = None
    if "active_trailer_movie" not in st.session_state:
        st.session_state.active_trailer_movie = None
    if "selected_mood_label" not in st.session_state:
        st.session_state.selected_mood_label = "None"

init_session_states()

# 3. Inject CSS Theme
inject_netflix_theme()

# 4. Premium Sidebar Navigation
def render_sidebar():
    watchlist = st.session_state.setdefault("watchlist", [])
    watchlist_count = len(watchlist)
    
    with st.sidebar:
        # Custom Minimalist Premium Vector SVG Logo and Luxury Typography
        st.markdown("""
            <div style="text-align: center; margin-top: 0.5rem; margin-bottom: 1rem;">
                <svg width="48" height="48" viewBox="0 0 100 100" style="margin: 0 auto; filter: drop-shadow(0 4px 12px rgba(229, 9, 20, 0.15));">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#e50914" stroke-width="2.5" opacity="0.9" />
                    <circle cx="50" cy="50" r="34" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" stroke-dasharray="10 5" />
                    <polygon points="44,36 66,50 44,64" fill="#ffffff" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));" />
                </svg>
                <h1 style="font-family: 'Space Grotesk', sans-serif !important; font-size: 1.8rem; font-weight: 800 !important; color: #ffffff; margin: 8px 0 0 0; letter-spacing: 4px; text-transform: uppercase;">
                    CineMatch
                </h1>
                <p style="color: #8e8e93; font-size: 0.62rem; margin: 2px 0 0 0; text-transform: uppercase; letter-spacing: 3px; font-weight: 700; font-family: 'Space Grotesk', sans-serif !important;">
                    AI Discovery Engine
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: rgba(255, 255, 255, 0.05); margin: 0 0 1rem 0;'>", unsafe_allow_html=True)
        st.caption("🧭 Explore Platform")
        
        # Navigation Options with Glowing active bullet markers
        nav_options = ["🏠 Home Landing", "🎯 AI Matcher", "💖 My Watchlist", "💡 Architecture Info"]
        page_mapping = {
            "🏠 Home Landing": "Home",
            "🎯 AI Matcher": "Recommend",
            "💖 My Watchlist": "Watchlist",
            "💡 Architecture Info": "About"
        }
        reverse_mapping = {v: k for k, v in page_mapping.items()}
        
        # Sync the selection state
        active_label = reverse_mapping.get(st.session_state.active_page, "🏠 Home Landing")
        active_index = nav_options.index(active_label)
        
        selected_nav = st.radio(
            "Navigation Menu",
            options=nav_options,
            index=active_index,
            label_visibility="collapsed"
        )
        
        # Route mapping
        new_page = page_mapping[selected_nav]
        if new_page != st.session_state.active_page:
            st.session_state.active_page = new_page
            # Reset active spotlights
            st.session_state.selected_movie_details = None
            st.session_state.active_trailer_movie = None
            st.rerun()
            
        st.markdown("<hr style='border-color: rgba(255, 255, 255, 0.05); margin: 0.5rem 0 1rem 0;'>", unsafe_allow_html=True)
        st.caption("📊 Platform Statistics")
        
        # Compact Horizontal Stats Flex Grid
        st.markdown(f"""
            <div style="display: flex; gap: 8px; justify-content: space-between; margin-bottom: 0.5rem;">
                <div class="sidebar-stat-card" style="flex: 1; padding: 6px 4px;">
                    <div class="sidebar-stat-val" style="font-size: 0.95rem;">45.4K</div>
                    <div class="sidebar-stat-label" style="font-size: 0.55rem; letter-spacing: 0.5px;">Titles</div>
                </div>
                <div class="sidebar-stat-card" style="flex: 1; padding: 6px 4px;">
                    <div class="sidebar-stat-val" style="font-size: 0.95rem;">{watchlist_count}</div>
                    <div class="sidebar-stat-label" style="font-size: 0.55rem; letter-spacing: 0.5px;">Saved</div>
                </div>
                <div class="sidebar-stat-card" style="flex: 1; padding: 6px 4px;">
                    <div class="sidebar-stat-val" style="font-size: 0.95rem;">&lt;100ms</div>
                    <div class="sidebar-stat-label" style="font-size: 0.55rem; letter-spacing: 0.5px;">Speed</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: rgba(229, 9, 20, 0.15); margin: 1rem 0;'>", unsafe_allow_html=True)
        st.caption("🛰️ Server Settings")
        
        # TMDB status indicators
        if is_api_key_configured():
            st.markdown("""
                <div style="background: rgba(46, 204, 113, 0.1); border: 1px solid rgba(46, 204, 113, 0.3); padding: 12px; border-radius: 8px;">
                    <div style="color: #2ecc71; font-weight: bold; font-size: 0.85rem; display: flex; align-items: center; gap: 6px;">
                        <span>🟢</span> TMDB API CONNECTED
                    </div>
                    <p style="color: #b3b3b3; font-size: 0.75rem; margin: 4px 0 0 0; line-height: 1.4;">
                        High-quality 4K backdrops, trailers, and trending metrics unlocked!
                    </p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: rgba(229, 9, 20, 0.08); border: 1px solid rgba(229, 9, 20, 0.3); padding: 12px; border-radius: 8px;">
                    <div style="color: #ff4d4d; font-weight: bold; font-size: 0.85rem; display: flex; align-items: center; gap: 6px;">
                        <span>⚠️</span> SANDBOX MODE ACTIVE
                    </div>
                    <p style="color: #b3b3b3; font-size: 0.75rem; margin: 4px 0 0 0; line-height: 1.4;">
                        Running with local mock suites. Add <code>TMDB_API_KEY</code> in <code>.env</code> file to enable complete global 4K trailer streaming!
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)

# 5. Core Application Main Routing Loop
def main():
    render_sidebar()
    
    # Route view drawing
    active_page = st.session_state.active_page
    
    if active_page == "Home":
        render_home_view()
    elif active_page == "Recommend":
        render_recommend_view()
    elif active_page == "Watchlist":
        render_watchlist_view()
    elif active_page == "About":
        render_about_view()

if __name__ == "__main__":
    main()
