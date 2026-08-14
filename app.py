import logging
import streamlit as st
from components.ui import inject_netflix_theme
from services.tmdb_client import get_api_status, STATUS_CONNECTED, STATUS_INVALID, STATUS_UNREACHABLE
from views.home import render_home_view
from views.recommend import render_recommend_view
from views.watchlist import render_watchlist_view
from views.about import render_about_view

# Structured logging (replaces scattered print debugging).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)

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
    # Custom sidebar toggle state ("expanded" | "collapsed") — drives the
    # premium open/close experience without Streamlit's native collapse icon.
    if "cm_sidebar_state" not in st.session_state:
        st.session_state.cm_sidebar_state = "expanded"

init_session_states()

# 3. Inject CSS Theme
inject_netflix_theme()

# 4. Premium Sidebar Navigation
SIDEBAR_LOGO_HTML = """
    <div class="cm-logo">
        <svg width="42" height="42" viewBox="0 0 100 100" aria-hidden="true">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#e50914" stroke-width="2.5" opacity="0.9" />
            <circle cx="50" cy="50" r="34" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" stroke-dasharray="10 5" />
            <polygon points="44,36 66,50 44,64" fill="#ffffff" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));" />
        </svg>
        <div>
            <div class="cm-logo-name">CineMatch</div>
            <div class="cm-logo-sub">AI Discovery Engine</div>
        </div>
    </div>
"""


def render_sidebar_expand_control():
    """Floating expand affordance shown only while the sidebar is collapsed.

    When collapsed, the sidebar section is hidden via CSS so the main canvas
    regains the full width naturally; this floating button is the only way
    back in (it re-runs the script with the sidebar state restored).
    """
    if st.session_state.get("cm_sidebar_state") != "collapsed":
        return
    with st.container():
        st.markdown('<div class="cm-sidebar-expand-marker"></div>', unsafe_allow_html=True)
        if st.button("☰", key="cm_expand_sidebar_btn",
                     help="Expand the sidebar navigation", width="stretch"):
            st.session_state.cm_sidebar_state = "expanded"
            st.rerun()


def render_sidebar():
    if st.session_state.get("cm_sidebar_state") == "collapsed":
        # Collapsed: hide the sidebar entirely (main content expands naturally,
        # the floating ☰ control restores it). The default Streamlit collapse
        # button stays removed, so no material-icon ligature can leak.
        st.markdown(
            '<style>section[data-testid="stSidebar"]{display:none !important;}</style>',
            unsafe_allow_html=True,
        )
        return

    watchlist = st.session_state.setdefault("watchlist", [])
    watchlist_count = len(watchlist)

    with st.sidebar:
        # Custom premium vector logo lockup + collapse control
        logo_col, collapse_col = st.columns([8.4, 1.6], gap="small")
        with logo_col:
            st.markdown(SIDEBAR_LOGO_HTML, unsafe_allow_html=True)
        with collapse_col:
            st.markdown('<div class="cm-side-collapse-marker"></div>', unsafe_allow_html=True)
            if st.button("❮", key="cm_collapse_sidebar_btn",
                         help="Collapse the sidebar and give content the full width",
                         width="stretch"):
                st.session_state.cm_sidebar_state = "collapsed"
                st.rerun()

        # Navigation
        st.markdown('<div class="cm-side-caption">Navigate</div>', unsafe_allow_html=True)
        
        nav_options = ["Home Landing", "AI Matcher", "My Watchlist", "Architecture Info"]
        page_mapping = {
            "Home Landing": "Home",
            "AI Matcher": "Recommend",
            "My Watchlist": "Watchlist",
            "Architecture Info": "About"
        }
        reverse_mapping = {v: k for k, v in page_mapping.items()}
        
        # Sync the selection state
        active_label = reverse_mapping.get(st.session_state.active_page, "Home Landing")
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
            
        # Platform statistics
        st.markdown('<div class="cm-side-caption">Statistics</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="cm-stats">
                <div class="cm-stat">
                    <div class="cm-stat-value">42.1K</div>
                    <div class="cm-stat-label">Titles</div>
                </div>
                <div class="cm-stat">
                    <div class="cm-stat-value">{watchlist_count}</div>
                    <div class="cm-stat-label">Saved</div>
                </div>
                <div class="cm-stat">
                    <div class="cm-stat-value">&lt;100ms</div>
                    <div class="cm-stat-label">Speed</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # TMDB connection status card (network-validated, never "key present = connected")
        st.markdown('<div class="cm-side-caption">System</div>', unsafe_allow_html=True)
        
        api_status = get_api_status()
        if api_status == STATUS_CONNECTED:
            st.markdown("""
                <div class="tmdb-status tmdb-ok">
                    <div class="tmdb-head"><span class="tmdb-dot"></span><span>TMDB Connected</span></div>
                    <div class="tmdb-sub">Live movie metadata enabled.</div>
                </div>
            """, unsafe_allow_html=True)
        elif api_status in (STATUS_INVALID, STATUS_UNREACHABLE):
            st.markdown("""
                <div class="tmdb-status tmdb-warn">
                    <div class="tmdb-head"><span class="tmdb-dot"></span><span>TMDB API Key Issue</span></div>
                    <div class="tmdb-sub">The configured key was rejected or TMDB is unreachable. Showing honest local dataset data until the key works.</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="tmdb-status tmdb-off">
                    <div class="tmdb-head"><span class="tmdb-dot"></span><span>Offline Mode</span></div>
                    <div class="tmdb-sub">No valid TMDB_API_KEY detected. Running on real local dataset data. Add your key in .env to unlock live backdrops and trailers.</div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown('<div class="cm-side-foot">CineMatch v2.2.0 · Powered by Streamlit</div>', unsafe_allow_html=True)

# 5. Core Application Main Routing Loop
def main():
    render_sidebar()
    render_sidebar_expand_control()
    
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
