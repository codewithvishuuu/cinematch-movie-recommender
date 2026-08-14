import streamlit as st
from components.ui import render_section_header

def render_about_view():
    """Renders the ultimate, premium cinematic about page detailing the ML pipeline."""
    st.markdown("""
        <h1 class="cm-page-title">Platform Architecture &amp; ML Science</h1>
        <p class="cm-page-sub">
            A detailed exploration of the mathematical vector models and high-throughput streaming systems powering CineMatch.
        </p>
    """, unsafe_allow_html=True)
    
    # 1. Pipeline Timeline Workflow Grid
    render_section_header("AI Recommendation Pipeline")
    
    st.markdown("""
        <div class="cm-panel cm-panel-accent" style="margin-bottom: 2rem;">
            <div style="display: flex; flex-direction: column; gap: 22px;">
                <div class="cm-step">
                    <div class="cm-step-num">1</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size: 1.1rem;">Text Metadata Tokenization</h4>
                        <p style="margin: 0; color: #a6a6b2; font-size: 0.9rem; line-height: 1.65;">
                            We synthesize raw descriptors (story plot summaries, genres, tagline keywords) into high-fidelity "tags" for <b>42,141 movies</b>.
                            The system processes these features using character and word-level tokenizers.
                        </p>
                    </div>
                </div>
                <div class="cm-step">
                    <div class="cm-step-num">2</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size: 1.1rem;">TF-IDF Vector Space Modeling</h4>
                        <p style="margin: 0; color: #a6a6b2; font-size: 0.9rem; line-height: 1.65;">
                            <b>Term Frequency-Inverse Document Frequency (TF-IDF)</b> converts this rich textual content into mathematical vectors. 
                            It reduces weights for highly common words (like "the" or "movie") and raises weight parameters for key story-defining elements (like "spacetime" or "heist").
                        </p>
                    </div>
                </div>
                <div class="cm-step">
                    <div class="cm-step-num">3</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size: 1.1rem;">Cosine Angular Similarities</h4>
                        <p style="margin: 0; color: #a6a6b2; font-size: 0.9rem; line-height: 1.65;">
                            To discover storyline duplicates, we measure the cosine angle between multidimensional movie vectors:
                            <br>
                            <code style="background: rgba(0,0,0,0.4); color: #ff5a63; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; display: inline-block; margin-top: 5px;">Similarity = (A · B) / (||A|| ||B||)</code>
                            <br>
                            This yields a precise, scalar resemblance value (between 0.0 and 1.0) indicating storytelling overlap.
                        </p>
                    </div>
                </div>
                <div class="cm-step">
                    <div class="cm-step-num">4</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size: 1.1rem;">Top 100 Re-ranking &amp; Hybrid Boosting</h4>
                        <p style="margin: 0; color: #a6a6b2; font-size: 0.9rem; line-height: 1.65;">
                            We slice the top 100 most storyline-similar movies first, guaranteeing high baseline matching relevance. 
                            Then, we inject dynamic boosts (15% Popularity + 15% Rating) along with real-time psychological mood filters to re-rank outcomes.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. Tech Stack Cards
    render_section_header("Platform Tech Stack")
    
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    
    with c1:
        st.markdown("""
            <div class="cm-tech-card">
                <div class="cm-tech-icon">🐍</div>
                <h5 class="cm-tech-name">Python Runtime</h5>
                <p class="cm-tech-desc">Core algorithmic execution environment for vector algebra and numerical operations.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
            <div class="cm-tech-card">
                <div class="cm-tech-icon">⚡</div>
                <h5 class="cm-tech-name">Streamlit Core</h5>
                <p class="cm-tech-desc">Orchestrates state coordination, navigation, and customizable UI element drawers.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
            <div class="cm-tech-card">
                <div class="cm-tech-icon">📊</div>
                <h5 class="cm-tech-name">Scikit-Learn</h5>
                <p class="cm-tech-desc">Precomputes sparse story TF-IDF text features and cosine vector calculations.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with c4:
        st.markdown("""
            <div class="cm-tech-card">
                <div class="cm-tech-icon">🛰️</div>
                <h5 class="cm-tech-name">TMDB Aggregator</h5>
                <p class="cm-tech-desc">Active, cached REST API integration for trailers, 4K banners, runtimes, and ratings.</p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 3. Creator and Architecture Guide Section
    c_left, c_right = st.columns([6, 4], gap="large")
    
    with c_left:
        st.markdown("""
            <div class="cm-panel" style="padding: 30px;">
                <h3 class="cm-panel-title">Architectural Pipeline</h3>
                <p style="color:#d9d9d9; line-height:1.7; font-size: 0.95rem;">
                    The platform leverages state-caching algorithms via <code>@st.cache_resource</code> to retain the 29MB dataset and the 18MB similarity sparse matrix cleanly in process memory once, enabling a latency below <b>100ms</b> on subsequent lookups.
                </p>
                <h4 style="color:#ffffff; margin-bottom:10px;">🛡️ Real-Time Resiliency Layer:</h4>
                <ul style="color:#b3b3b3; line-height:1.7; font-size:0.92rem; margin-bottom:0; padding-left:20px;">
                    <li><b>Fuzzy corrects:</b> Title autocomplete autocorrects spelling inconsistencies.</li>
                    <li><b>Trace logger:</b> Safe CP1252-safe logging prints details cleanly without process crashes.</li>
                    <li><b>Active fallback:</b> Sandboxed fallbacks guarantee that valid suite titles (Interstellar, Heat, Toy Story, Avengers, Inception, Dark Knight) always load beautiful assets.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with c_right:
        st.markdown("""
            <div class="cm-panel cm-panel-accent" style="text-align: center;">
                <h3 class="cm-panel-title">App Info</h3>
                <div style="font-size: 0.95rem; color: #a6a6b2; margin-bottom: 20px;">
                    <b>CineMatch Platform</b> v2.2.0
                </div>
                <div style="text-align: left; color: #a6a6b2; font-size: 0.9rem; line-height: 2;">
                    <b>Frontend:</b> Streamlit (Python)<br>
                    <b>Theme:</b> CineMatch Cinematic Dark<br>
                    <b>Database Size:</b> 42,141 titles<br>
                    <b>Core Libraries:</b> Pandas, Scikit-learn, Requests<br>
                    <b>API Source:</b> Live TMDB API Integration<br>
                </div>
                <hr style="border-color: rgba(229, 9, 20, 0.2); margin: 20px 0;">
                <div style="font-size: 0.85rem; color: #63636e;">
                    Designed and optimized by Vishal Kumar &amp; Antigravity.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
