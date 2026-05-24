# 🍿 CineMatch — Premium AI Movie Recommendation Engine

CineMatch is a production-grade, highly optimized hybrid AI movie recommendation platform wrapped in an immersive, Netflix-inspired dark-red glassmorphic dashboard. Powered by a 29MB machine learning engine querying 45,447 catalogued titles in constant-time, the platform integrates high-dimensional Term Frequency-Inverse Document Frequency (TF-IDF) storyline vectorization with global popularity metrics, TMDB live API signals, and dynamic steering filters. CineMatch parses semantic narratives, adjusts matching matrices for real-time psychological mood preferences, and streams high-fidelity 4K posters and YouTube trailers directly inside fluid, responsive viewports.

## 🚀 Live Demo

Experience the intelligent recommendation engine live: **[cinematch-ai.streamlit.app](https://cinematch-movie-recommender-bqzsppgvepmahksda8qxg9.streamlit.app/#popular-movies)**


## ✨ Features

- **Semantic Recommendation Engine**: Computes high-dimensional plot similarities between movies to discover narrative counterparts with constant-time hash lookups.
- **TF-IDF Vector Similarity**: Tokenizes overviews, genres, and taglines into sparse matrices using term frequency-inverse document frequency to extract core story elements.
- **TMDB Live Integration**: Aggregates high-quality 4K poster backdrops, dynamic metadata, runtimes, cast details, and video trailer streams via resilient TMDB API calls.
- **Typo-Correcting Autocomplete**: Dynamic sequence-matching search input with roman-numeral sequel converters and instant suggestion chip matrices.
- **Dynamic Hero Spotlight**: Full-width cinematic billboard spotlight showcasing trending blockbusters with video players and interactive controls.
- **Netflix Cinematic UI**: Immersive glassmorphic design featuring deep obsidian backdrops, neon-crimson accents, customized carousels, and glowing active states.
- **Psychological Mood Steering**: Shifts the recommendation vector matrices in real-time by applying soft-weight adjustments ($\approx +20\%$ score shift) toward target mood genres.
- **Responsive Engineering**: Universal adaptive flex layouts, fluid `clamp()` sizing, parent-selector CSS overrides, and mobile-friendly touch targets.
- **Stateful Watchlist**: Managed local watchlist allowing users to bookmark and track films statefully across pages with zero server-side latency.
- **Resilient Caching Systems**: Double-layered memory caching using `@st.cache_resource` for ML assets and `@st.cache_data` (24h TTL) for API payloads.

---

## 🎨 UI Showcase

| 🏠 Home Landing Billboard | 🎯 AI Movie Intelligence Laboratory | 📱 Universal Responsive Reflow |
| :---: | :---: | :---: |
| ![Home Preview](preview-home.png) | ![AI Lab Preview](preview-ai-lab.png) | ![Mobile Responsive Preview](preview-mobile.png) |
| *Immersive featured backdrops and slider rows* | *Active autocomplete search and parameter sliders* | *Optimized touch configurations for mobile browsers* |

---

## 🧠 AI Recommendation Pipeline

CineMatch utilizes an advanced content-aware hybrid pipeline to formulate recommendation arrays in under **10 milliseconds**:

1. **Metadata Aggregation**: Merges plot overviews, genres, taglines, and cast info into unique document corpora.
2. **Semantic Vectors**: Fits term frequency-inverse document frequency (TF-IDF) tokenizers to project documents into high-dimensional vector spaces.
3. **Cosine Similarity**: Resolves the angular distance between the target film vector and all database vectors to extract the top 100 most storyline-similar items.
4. **Hybrid Reranking**: Combines semantic alignment (70% weight) with normalized popularity and rating indices (30% weight) to bypass content bias.
5. **Mood Steer Boosting**: Modifies target genre coordinates by +20% depending on selected emotional mood overrides.
6. **Caching Pipeline**: Hooks memory caches (`@st.cache_resource`) to retain dataframes and vector weights, while caching REST calls (`@st.cache_data`) for 24 hours to secure API latency.

---

## 🛠️ Technology Stack

| Architectural Layer | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Language Runtime** | Python 3.10+ | Primary algorithmic execution and backend pipelines |
| **Interactive UI** | Streamlit v1.32+ | Interactive state orchestration, widgets, and router loops |
| **Machine Learning Core** | Scikit-Learn (TF-IDF) | Storyline vector vocabulary tokenizers and sparse matrices |
| **Vector Algebra** | NumPy & Pandas | Constant-time high-dimensional array arithmetic and fuzzy matching |
| **High-Fidelity Assets** | TMDB REST API | Real-time 4K image backdrops, cast listings, and YouTube trailer links |
| **Styling & Layout** | Vanilla CSS3 / HTML5 | Custom glassmorphism, responsive grids reflows, and clamp() typography |

---

## 📂 Project Architecture

```
cinematch-movie-recommender/
├── app.py                      # Root app coordinator; handles session states, sidebar, and view routing
├── requirements.txt            # Streamlined third-party ML and web libraries
├── .env.example                # Configuration template for external TMDB keys
│
├── config/                     # Configuration Engine
│   └── settings.py             # Global constants, TMDB base endpoints, and API validator guards
│
├── assets/                     # Premium Stylesheets
│   └── main.css                # Obsidian glassmorphic CSS; custom carousels, responsive grid overrides
│
├── services/                   # Business Logic & API Layer
│   ├── tmdb_service.py         # TMDB client; aggregates trailer feeds and cast lists with 24-hour caches
│   └── search_service.py       # Typo-correcting search pipeline; queries local dataset with TMDB live fallbacks
│
├── ml/                         # Machine Learning Core
│   ├── recommender.py          # Hybrid recommender; precomputes normalized popularity and applies mood-aware soft vectors
│   ├── df.pkl                  # Pickled 45,447 movie metadata records dataframe (29.5 MB)
│   ├── indices.pkl             # O(1) Constant-time hash map title-to-index mapper (1.4 MB)
│   ├── tfidf.pkl               # Pickled TF-IDF vectorizer configuration
│   └── tfidf_matrix.pkl        # Precomputed sparse matrix representing story plot vectors in high-dimensional space
│
├── components/                 # Decoupled UI Modules
│   ├── ui.py                   # Immersive Netflix layouts; details panel overlays, movie poster cards, video borders
│   ├── movie_hero.py           # Spotlight blockbuster billboard component with validation logs
│   ├── search_bar.py           # Autocomplete input layout with 2x5 quick-select trending suggestion chips
│   └── autocomplete_dropdown.py # Dropdown result card panel; displays live match ratings, years, and selection triggers
│
└── views/                      # Widescreen View Controllers
    ├── home.py                 # Multi-carousel page displaying curated trending lists and scifi/horror sliders
    ├── recommend.py            # AI Lab dashboard featuring parameters, multiselect filters, and mood steers
    ├── watchlist.py            # Managed watchlist workspace page complete with dynamic empty-state prompts
    └── about.py                # Tech stack guide; visual workflow pipelines and system performance audits
```

---

## 📱 Responsive Engineering

CineMatch replaces basic Streamlit columns with custom responsive styling to deliver seamless viewport adaptation:

- **Adaptive CSS Grids**: Re-arranges layout elements automatically from 6 columns on widescreen displays to 3 on tablets and a full-width vertical stack on mobile.
- **Responsive Typography**: Leverages CSS `clamp()` bounds to scale headers and movie captions gracefully across all screen sizes without truncation or overlaps.
- **Mobile Touch Targets**: Automatically transforms small card buttons into full-width stacked touch regions under 520px to prevent misclicks on compact phone screens.
- **Viewport Overflow Fixes**: Employs absolute `white-space: nowrap` and `overflow-x: hidden` rules to eliminate unwanted horizontal scrolls.

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/codewithvishuuu/cinematch-movie-recommender.git
cd cinematch-movie-recommender

# Set up environment configuration
cp .env.example .env
# Open .env and populate your TMDB_API_KEY="your_key"

# Install machine learning and web frameworks
pip install -r requirements.txt

# Launch the cinematic platform
streamlit run app.py
```

---

## ☁️ Deployment

- **GitHub Integration**: Connect your branch directly to Streamlit Community Cloud for automated, continuous production updates.
- **Streamlit Cloud Config**: Set `TMDB_API_KEY` under the advanced secrets parameters panel (`Secrets.toml`).
- **Resilient Fallback Mode**: If deployed without environment variables, the engine safely flags sandboxed operations, using offline local datasets and mock image cards.

---

## 👨‍💻 Developer

Engineered and maintained with care by **Vishal Kumar**.

---

## ⭐ Support

If this premium AI recommender or its glassmorphic layout has helped your research, please give this repository a ⭐ on GitHub!
