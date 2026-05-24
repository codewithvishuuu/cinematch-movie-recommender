import streamlit as st

def render_about_view():
    """Renders the ultimate, premium cinematic about page detailing the ML pipeline."""
    st.markdown("""
        <div class="section-title-container" style="margin-top: 1rem;">
            <h1 style="margin: 0; font-size: 2.2rem; font-family:'Montserrat', sans-serif;">💡 Platform Architecture & ML Science</h1>
        </div>
        <p style="color: #b3b3b3; font-size: 1.1rem; margin-bottom: 2.5rem;">
            A detailed exploration of the mathematical vector models and high-throughput streaming systems powering CineMatch.
        </p>
    """, unsafe_allow_html=True)
    
    # 1. Pipeline Timeline Workflow Grid (Glassmorphism layout)
    st.markdown("### 🧬 AI Recommendation Pipeline")
    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(229, 9, 20, 0.20); padding: 30px; border-radius: 12px; margin-bottom: 2rem;">
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div style="display: flex; gap: 15px; align-items: flex-start;">
                    <div style="background: #e50914; color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; flex-shrink: 0; box-shadow: 0 0 10px #e50914;">1</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size:1.15rem;">Text Metadata Tokenization</h4>
                        <p style="margin: 0; color: #b3b3b3; font-size: 0.92rem; line-height: 1.6;">
                            We synthesize raw descriptors (story plot summaries, genres, tagline keywords) into high-fidelity "tags" for <b>45,447 movies</b>. 
                            The system processes these features using character and word-level tokenizers.
                        </p>
                    </div>
                </div>
                <div style="display: flex; gap: 15px; align-items: flex-start;">
                    <div style="background: #e50914; color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; flex-shrink: 0; box-shadow: 0 0 10px #e50914;">2</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size:1.15rem;">TF-IDF Vector Space Modeling</h4>
                        <p style="margin: 0; color: #b3b3b3; font-size: 0.92rem; line-height: 1.6;">
                            <b>Term Frequency-Inverse Document Frequency (TF-IDF)</b> converts this rich textual content into mathematical vectors. 
                            It reduces weights for highly common words (like "the" or "movie") and raises weight parameters for key story-defining elements (like "spacetime" or "heist").
                        </p>
                    </div>
                </div>
                <div style="display: flex; gap: 15px; align-items: flex-start;">
                    <div style="background: #e50914; color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; flex-shrink: 0; box-shadow: 0 0 10px #e50914;">3</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size:1.15rem;">Cosine Angular Similarities</h4>
                        <p style="margin: 0; color: #b3b3b3; font-size: 0.92rem; line-height: 1.6;">
                            To discover storyline duplicates, we measure the cosine angle between multidimensional movie vectors:
                            <br>
                            <code style="background: rgba(0,0,0,0.4); color: #ff4d4d; padding: 2px 6px; border-radius: 4px; font-size: 0.82rem; display: inline-block; margin-top: 5px;">Similarity = (A · B) / (||A|| ||B||)</code>
                            <br>
                            This yields a precise, scalar resemblance value (between 0.0 and 1.0) indicating storytelling overlap.
                        </p>
                    </div>
                </div>
                <div style="display: flex; gap: 15px; align-items: flex-start;">
                    <div style="background: #e50914; color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; flex-shrink: 0; box-shadow: 0 0 10px #e50914;">4</div>
                    <div>
                        <h4 style="margin: 0 0 5px 0; color: #ffffff; font-size:1.15rem;">Top 100 Re-ranking & Hybrid Boosting</h4>
                        <p style="margin: 0; color: #b3b3b3; font-size: 0.92rem; line-height: 1.6;">
                            We slice the top 100 most storyline-similar movies first, guaranteeing high baseline matching relevance. 
                            Then, we inject dynamic boosts (15% Popularity + 15% Rating) along with real-time psychological mood filters to re-rank outcomes.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 2. Tech Stack Cards
    st.markdown("### 🛠️ Platform Tech Stack")
    
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    
    with c1:
        st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🐍</div>
                <h5 style="margin: 0 0 5px 0; font-size: 1.05rem;">Python Runtime</h5>
                <p style="margin: 0; color: #b3b3b3; font-size: 0.8rem; line-height: 1.4;">Core algorithmic execution environment for vector algebra and numerical operations.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">⚡</div>
                <h5 style="margin: 0 0 5px 0; font-size: 1.05rem;">Streamlit Core</h5>
                <p style="margin: 0; color: #b3b3b3; font-size: 0.8rem; line-height: 1.4;">Orchestrates state coordination, navigation, and customizable UI element drawers.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">📊</div>
                <h5 style="margin: 0 0 5px 0; font-size: 1.05rem;">Scikit-Learn</h5>
                <p style="margin: 0; color: #b3b3b3; font-size: 0.8rem; line-height: 1.4;">Precomputes sparse story TF-IDF text features and cosine vector calculations.</p>
            </div>
        """, unsafe_allow_html=True)
        
    with c4:
        st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255,255,255,0.05); padding: 20px; border-radius: 8px; text-align: center; height: 180px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🛰️</div>
                <h5 style="margin: 0 0 5px 0; font-size: 1.05rem;">TMDB Aggregator</h5>
                <p style="margin: 0; color: #b3b3b3; font-size: 0.8rem; line-height: 1.4;">Active, cached REST API integration for trailers, 4K banners, runtimes, and ratings.</p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 3. Creator and Architecture Guide Section
    c_left, c_right = st.columns([6, 4], gap="large")
    
    with c_left:
        st.markdown("""
            <div class="glass-panel" style="padding: 30px;">
                <h3 style="margin-top:0; margin-bottom:15px; color:#ff4d4d; font-family:'Montserrat',sans-serif;">🔬 Architectural Pipeline</h3>
                <p style="color:#d9d9d9; line-height:1.7; font-size: 0.95rem;">
                    The platform leverages state-caching algorithms via <code>@st.cache_resource</code> to retain the 29MB dataset and the 18MB similarity sparse matrix cleanly in process memory once, enabling a latency of **less than 100ms** on subsequent lookups.
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
            <div style="background: rgba(229, 9, 20, 0.04); border: 1px solid rgba(229, 9, 20, 0.15); padding: 30px; border-radius: 12px; text-align: center;">
                <h3 style="color: #ffffff; margin-top: 0; margin-bottom: 10px; font-family:'Montserrat',sans-serif;">🚀 App Info</h3>
                <div style="font-size: 0.95rem; color: #b3b3b3; margin-bottom: 20px;">
                    <b>CineMatch Platform</b> v2.2.0
                </div>
                <div style="text-align: left; color: #b3b3b3; font-size: 0.9rem; line-height: 2;">
                    <b>Frontend:</b> Streamlit (Python)<br>
                    <b>Theme:</b> Netflix Cinematic CSS<br>
                    <b>Database Size:</b> 45,447 titles<br>
                    <b>Core Libraries:</b> Pandas, Scikit-learn, Requests<br>
                    <b>API Source:</b> Live TMDB API Integration<br>
                </div>
                <hr style="border-color: rgba(229, 9, 20, 0.2); margin: 20px 0;">
                <div style="font-size: 0.85rem; color: #8c8c8c;">
                    Designed and optimized by Vishal Kumar & Antigravity.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
