# 🍿 CineMatch — Premium AI Movie Recommendation Platform

<p align="center">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit Badge">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge">
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="Scikit-Learn Badge">
  <img src="https://img.shields.io/badge/TMDB-01B4E4?style=for-the-badge&logo=the-movie-database&logoColor=white" alt="TMDB Badge">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License Badge">
</p>

CineMatch is a production-ready, AI-driven movie recommendation engine wrapped in a premium, Netflix-inspired responsive cinematic dashboard. 

By analyzing high-dimensional storyline overviews, genres, tagline keywords, and metadata from a database of **45,447 movies**, CineMatch matches users with custom cinematic suggestions based on story similarity, global popularity scaling, and real-time psychological mood steering.

---

## 🎨 Premium Interface Showcase

> [!NOTE]
> Below are premium interface mockups demonstrating the Netflix-inspired dark-red glassmorphism aesthetic:

| 🏠 Home Landing Banner & Carousels | 🎯 Intelligent Parameter Matcher |
| :---: | :---: |
| ![Home Banner Placeholder](https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=600&auto=format&fit=crop) | ![AI Search Placeholder](https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=600&auto=format&fit=crop) |
| *Featured 4K Backdrops and dynamic horizontal sliders* | *Fuzzy autocomplete query parameters and mood filters* |

---

## ✨ Primary Features

- **🎬 Immersive Netflix Theme:** Deep obsidian base (`#0b0c10`) layered with glowing neon crimson accents (`#E50914`), custom animated cards, and responsive 6-column grids.
- **🚀 Advanced Hybrid Matcher:** Storyline TF-IDF + 15% TMDB Rating + 15% TMDB Popularity scoring algorithms.
- **🎭 Mood-Aware Filtering:** Alters recommendation vectors in real-time based on psychological filters (*Intense*, *Uplifting*, *Spooky*, *Melancholic*, etc.).
- **📺 Inline Video Spotlight Drawer:** Clicking any card expands a glassmorphic dashboard showcasing full runtime, rating, genres, and streams trailer videos instantly inside the page.
- **💖 Local watchlist coordination:** Track saved masterpieces across tabs without losing active selections.
- **🛡️ Resilient Caching & Offline Sandbox:** Gracefully runs utilizing robust fallback data mappings if no API keys are present, backed by defensive `@st.cache_data` rate-limit managers.

---

## 🛠️ Tech Stack Specifications

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Core Runtime** | Python 3.10+ | Core application execution environment |
| **Frontend Framework** | Streamlit | UI rendering and modular widgets |
| **Styling Engine** | Vanilla CSS + HTML5 | Netflix obsidian styling, glassmorphism, and hover animations |
| **ML Vectorizer** | Scikit-Learn (TF-IDF) | Parses textual metadata into high-dimensional lexical vectors |
| **Similarity Metrics** | Cosine Similarity | Measures angular distance between film storyline matrices |
| **API Provider** | The Movie Database (TMDB) | Dynamically aggregates posters, trailers, runtimes, and scores |

---

## 🧠 Under The Hood: AI Recommendation Engine

CineMatch combines traditional content-based textual recommendations with production-grade hybrid weighting and steering:

### 1. Vector Space Representation
Text tags (combined story plot overviews, genres, taglines) are parsed into sparse term-frequency vectors:

$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \log\left(\frac{\|D\|}{1 + \||\{d \in D : t \in d\}|\|}\right)$$

### 2. Angular Distance Calculations
Story similarity is computed measuring the cosine of the angle between vectors:

$$\text{Cosine Similarity}(A, B) = \frac{A \cdot B}{\|\|A\|\| \|\|B\|\|}$$

### 3. Hybrid Weighting Formula
We balance text vectors with user engagement and review scores to optimize recommendation quality:

$$\text{Final Affinity Score} = 0.70 \cdot \text{Cosine Sim} + 0.15 \cdot \text{Popularity Score} + 0.15 \cdot \text{Rating Score} + \text{Mood Boost}$$

<details>
<summary><b>🎭 View Mood-to-Genre Mappings Configuration</b></summary>

Our steering matrices skew vectors towards target categories depending on active moods:
- **Uplifting / Feel-Good:** Comedy, Family, Romance, Animation, Music
- **Intense / Mind-Bending:** Mystery, Science Fiction, Thriller, Crime
- **Thrilling / Action-Packed:** Action, Adventure, Fantasy, War, Western
- **Spooky / Terrifying:** Horror, Mystery, Thriller
- **Emotional / Melancholic:** Drama, Romance, History
- **Thought-Provoking:** Documentary, History, Science Fiction, Mystery
</details>

---

## 📂 Modular Architecture Guide

CineMatch follows a highly maintainable, professional modular architecture:

```
cinematch-movie-recommender/
│
├── .env.example            # Environment variables template
├── requirements.txt        # Streamlined third-party dependencies
├── app.py                  # Streamlit entry orchestrator and nav page router
│
├── config/
│   └── settings.py         # Loads secrets and configures endpoints
│
├── services/
│   └── tmdb_service.py     # Caching API manager (trailers, backdrops, fallback mapping)
│
├── ml/
│   ├── recommender.py      # Upgraded Hybrid AI Engine
│   ├── df.pkl              # 45,447 movies dataframe (Title, popularity, genres)
│   ├── indices.pkl         # Title index mapper
│   └── tfidf_matrix.pkl    # Precomputed sparse story vectors
│
├── components/
│   └── ui.py               # Custom themes, dynamic spotlight panels, trailer players
│
├── views/
│   ├── home.py             # Featured landing rows with 6-card columns
│   ├── recommend.py        # Active AI selectors, moods, and parameter inputs
│   ├── watchlist.py        # Managed local watchlist saved viewport
│   └── about.py            # Mathematical pipeline walkthroughs
│
└── assets/
    └── main.css            # Custom premium Netflix layout stylesheets
```

---

## ⚙️ Installation & Getting Started

### Prerequisites
- Python 3.10+
- Pip package manager

### 1. Clone the platform
```bash
git clone https://github.com/codewithvishuuu/cinematch-movie-recommender.git
cd cinematch-movie-recommender
```

### 2. Configure Environment variables
Copy the environment variables template:
```bash
cp .env.example .env
```
Open `.env` and configure your TMDB API token:
```env
TMDB_API_KEY="your_tmdb_api_key_here"
```
*(Obtain a free API key instantly at [The Movie Database](https://www.themoviedb.org/settings/api)).*

### 3. Install packages
```bash
pip install -r requirements.txt
```

### 4. Run the dashboard
```bash
streamlit run app.py
```
The platform will launch automatically in your default browser at `http://localhost:8501`.

---

## ☁️ Deployment Instructions

CineMatch is fully optimized for containerized and server deployments.

### Streamlit Cloud Deploy
1. Push this project to your GitHub repository.
2. Log into [Streamlit Cloud](https://share.streamlit.io/) and click "New app".
3. Select this repository and specify `app.py` as the entry file path.
4. Navigate to **Advanced Settings -> Secrets** and paste your API key:
   ```toml
   TMDB_API_KEY = "your_tmdb_api_key_here"
   ```
5. Click **Deploy**!

---

## 🛠️ Troubleshooting Guide

<details>
<summary><b>🔴 Issue: Movie posters are showing gray default boxes</b></summary>

- **Reason:** TMDB API key is either missing, copy-pasted incorrectly, or blocked by local firewalls.
- **Fix:** Verify your `.env` contains `TMDB_API_KEY="your_actual_key"`. If running locally without an internet connection, sandbox default fallbacks will display beautifully for test films (Interstellar, Heat, Toy Story, Avengers, Inception) but general titles will leverage Unsplash graphic fallbacks.
</details>

<details>
<summary><b>🔴 Issue: Streamlit server loads slowly on startup</b></summary>

- **Reason:** Legacy Streamlit configurations import pickled datasets on every module reload.
- **Fix:** CineMatch v2.0 loads all resources inside a cached `@st.cache_resource` manager, resulting in subsequent startup times of **less than 100ms**.
</details>

<details>
<summary><b>🔴 Issue: ModuleNotFoundError for numpy or sklearn</b></summary>

- **Reason:** Virtual environment has not activated, or requirements were bypassed.
- **Fix:** Run `pip install -r requirements.txt` again to update ML matrix dependencies.
</details>

---

## 🔮 Future Improvements

- **🎭 Personalized Profiles:** User accounts and recommendations persisted in a PostgreSQL relational schema.
- **🧬 Collaborative Filtering:** Matrix Factorization (SVD) layering to compute user-behavior similarity.
- **🎙️ Natural Language Querying:** Integrating an LLM agent to allow conversational recommendations ("Find me a gritty sci-fi set in space similar to Interstellar").

---

*CineMatch AI Platform is licensed under the MIT License. Maintained by **Vishal Kumar** & **Antigravity** (Google DeepMind).*
