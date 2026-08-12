"""CineMatch Recommendation Engine V2 — hybrid recommender.

Keeps the proven sparse TF-IDF content architecture and adds:
  - canonical genre similarity (Jaccard, multi-word aware)
  - quality-aware rating signal (dataset-mean-centered, evidence-shrunk)
  - a very small popularity signal (log-scaled, no vote_count fiction)
  - MMR-style diversity-aware re-ranking
  - deterministic search resolution (no first-row ambiguity)
  - evidence-based explanations derived only from available fields
  - calibrated relative match labels (percentile within the candidate pool)

Production compatibility surface (unchanged):
  df, indices, tfidf_matrix, get_recommendations(), get_all_movies(),
  get_all_genres(), get_moods(), fuzzy_find_movie().
"""
import os
import re
import pickle
import difflib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Data dir override is ONLY used by the benchmark harness to compare staged
# builds (ml_next) without touching the production files.
DATA_DIR = os.environ.get("CINEMATCH_ML_DIR") or BASE_DIR


def _load_pickle(name):
    with open(os.path.join(DATA_DIR, name), "rb") as f:
        return pickle.load(f)


# ---------------------------------------------------------------------------
# Canonical genres (Phase 3B)
# ---------------------------------------------------------------------------
MULTI_WORD_GENRES = ["Science Fiction", "TV Movie"]


def parse_genres(genres_val):
    """Parses the space-joined genre string into canonical genre names.

    Multi-word genres ('Science Fiction', 'TV Movie') stay single canonical
    tokens. Unknown tokens are preserved, never invented or removed.
    """
    if not genres_val or not isinstance(genres_val, str):
        return []
    s = genres_val.strip()
    if not s:
        return []
    for mw in MULTI_WORD_GENRES:
        s = re.sub(re.escape(mw), mw.replace(" ", "_"), s)
    return [tok.replace("_", " ") for tok in s.split()]


def _jaccard(a, b):
    """Jaccard similarity of two canonical genre sets (0.0 when either is empty)."""
    a = set(parse_genres(a))
    b = set(parse_genres(b))
    if not a or not b:
        return 0.0
    inter = a & b
    union = a | b
    return len(inter) / len(union) if union else 0.0


MOOD_GENRE_MAP = {
    "Uplifting / Feel-Good": ["Comedy", "Family", "Romance", "Animation", "Music"],
    "Intense / Mind-Bending": ["Science Fiction", "Mystery", "Thriller", "Crime"],
    "Thrilling / Action-Packed": ["Action", "Adventure", "Fantasy", "War", "Western"],
    "Spooky / Terrifying": ["Horror", "Mystery", "Thriller"],
    "Emotional / Melancholic": ["Drama", "Romance", "History"],
    "Thought-Provoking": ["Documentary", "History", "Science Fiction", "Mystery"],
}


@st.cache_resource(show_spinner=False)
def load_models():
    """Loads and caches dataset, indices, sparse TF-IDF matrix and vectorizer."""
    try:
        df = _load_pickle("df.pkl")
        indices = _load_pickle("indices.pkl")
        tfidf_matrix = _load_pickle("tfidf_matrix.pkl")
        vectorizer = _load_pickle("tfidf.pkl")

        df = df.reset_index(drop=True)

        # --- numeric conversions (defensive, deterministic) --------------
        df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce').fillna(0.0)
        df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0.0)

        # Popularity signal: log-scaled relative magnitude (never vote_count).
        log_pop = np.log1p(df['popularity'].to_numpy())
        log_pop_max = log_pop.max() if log_pop.size else 1.0
        df['norm_popularity'] = log_pop / (log_pop_max + 1e-8)

        # Quality signal: centered on the library mean, clipped, shrunk to 0
        # (neutral) when a movie has no rating evidence (vote_average<=0).
        # Evidence strength: with no vote_count available, a rating's
        # credibility is dampened for titles with negligible traction - credit
        # is scaled by (0.4 + 0.6*log-popularity rank). Transparent and based
        # only on fields actually present (vote_average, popularity).
        va = df['vote_average'].to_numpy()
        quality = np.clip((va - 6.0) / 4.0, -0.5, 1.0)
        quality[va <= 0.0] = 0.0
        credibility = 0.4 + 0.6 * df['norm_popularity'].to_numpy()
        df['quality'] = quality * credibility

        # Canonical genre parse cache (computed once, reused every query).
        df['genres_parsed'] = [parse_genres(g) for g in df['genres'].fillna('')]

        # --- search compatibility fields (unchanged from Phase 1/2) ------
        df['title_clean'] = df['title'].fillna('').astype(str).str.lower().str.strip()
        df['title_clean'] = df['title_clean'].str.replace(r'\s*\(\d{4}\)\s*$', '', regex=True)
        df['title_clean'] = df['title_clean'].str.replace(r'[^\w\s]', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
        df['title_strict'] = df['title_clean'].str.replace(r'\s+', '', regex=True)

        s_roman = df['title_strict']
        s_roman = s_roman.str.replace(r'\bpart\s+i\b', 'part 1', regex=True)
        s_roman = s_roman.str.replace(r'\bpart\s+ii\b', 'part 2', regex=True)
        s_roman = s_roman.str.replace(r'\bpart\s+iii\b', 'part 3', regex=True)
        s_roman = s_roman.str.replace(r'\bpart\s+iv\b', 'part 4', regex=True)
        s_roman = s_roman.str.replace(r'\bpart\s+v\b', 'part 5', regex=True)
        s_roman = s_roman.str.replace(r'\bii\b', '2', regex=True)
        s_roman = s_roman.str.replace(r'\biii\b', '3', regex=True)
        s_roman = s_roman.str.replace(r'\biv\b', '4', regex=True)
        s_roman = s_roman.str.replace(r'\bv\b', '5', regex=True)
        df['title_roman'] = s_roman

        df['norm_rating'] = df['norm_rating'] if 'norm_rating' in df.columns else 0.0

        # Feature-name cache for shared-term explanations (50k strings, once).
        try:
            features = np.asarray(vectorizer.get_feature_names_out())
        except Exception:
            features = np.asarray([])

        return df, indices, tfidf_matrix, vectorizer, features
    except Exception as e:
        print(f"Error loading model files: {e}")
        return pd.DataFrame(), pd.Series(), None, None, np.asarray([])


df, indices, tfidf_matrix, vectorizer, _FEATURES = load_models()


# ---------------------------------------------------------------------------
# Hybrid scoring weights (Phase 3D) — benchmarked against the BEFORE baseline
# ---------------------------------------------------------------------------
# content similarity (TF-IDF cosine)    : 0.60
# canonical genre Jaccard               : 0.18
# quality-aware rating signal           : 0.10
# log popularity signal                 : 0.08
W_CONTENT, W_GENRE, W_QUALITY, W_POP = 0.60, 0.18, 0.10, 0.08

# MMR diversification (Phase 3F): relevance keeps the majority of the weight.
MMR_LAMBDA = 0.75
CANDIDATE_POOL = 300   # hybrid candidates scored per query
MMR_POOL = 60          # pool fed to diversity re-ranking


def get_all_movies():
    """Returns a sorted list of all canonical movie titles."""
    if df.empty:
        return []
    return sorted(df['title'].dropna().unique().tolist())


def get_all_genres():
    """Returns the canonical genre vocabulary (multi-word genres intact)."""
    if df.empty or 'genres' not in df.columns:
        return []
    all_genres = set()
    for g in df['genres'].dropna():
        all_genres.update(parse_genres(g))
    return sorted(all_genres)


def get_moods():
    """Returns the supported interactive psychological mood filters."""
    return list(MOOD_GENRE_MAP.keys())


def fuzzy_find_movie(query_title):
    """Resolves a query to an exact canonical dataset title (deterministic)."""
    if df.empty or not query_title:
        return None

    titles = get_all_movies()
    query_clean = query_title.strip().lower()

    for title in titles:
        if title.lower().strip() == query_clean:
            return title

    query_normalized = re.sub(r'\s*\(\d{4}\)\s*$', '', query_clean)
    query_normalized = re.sub(r'[^\w\s]', '', query_normalized).strip()

    for title in titles:
        title_clean = title.lower().strip()
        title_normalized = re.sub(r'\s*\(\d{4}\)\s*$', '', title_clean)
        title_normalized = re.sub(r'[^\w\s]', '', title_normalized).strip()
        if title_normalized == query_normalized:
            return title

    year_match = re.search(r'\(?(\d{4})\)?$', query_clean)
    if year_match:
        target_year = year_match.group(1)
        query_without_year = re.sub(r'\s*\(?(\d{4})\)?$', '', query_clean).strip()
        sub_matches = [t for t in titles if query_without_year in t.lower().strip()]
        for t in sub_matches:
            df_rows = df[df['title'] == t]
            if not df_rows.empty:
                df_year = str(df_rows.iloc[0].get('release_date', ''))[:4]
                if df_year == target_year:
                    return t

    sub_matches = [title for title in titles if query_clean in title.lower().strip()]
    if sub_matches:
        sub_matches.sort(key=lambda x: abs(len(x) - len(query_title)))
        return sub_matches[0]

    fuzzy_matches = difflib.get_close_matches(query_title, titles, n=1, cutoff=0.55)
    if fuzzy_matches:
        return fuzzy_matches[0]

    return None


def _shared_story_terms(src_row, cand_row, top_k=2):
    """Top shared TF-IDF story terms between two rows (min-weight ranked).

    Uses only real content overlap; returns [] when there is none.
    """
    m = tfidf_matrix
    if m is None or not _FEATURES.size:
        return []
    a, b = m.indptr[src_row], m.indptr[src_row + 1]
    c, d = m.indptr[cand_row], m.indptr[cand_row + 1]
    si, sv = m.indices[a:b], m.data[a:b]
    ci, cv = m.indices[c:d], m.data[c:d]
    s_si, s_sv = si[np.argsort(si)], sv[np.argsort(si)]
    s_ci, s_cv = ci[np.argsort(ci)], cv[np.argsort(ci)]
    common = np.intersect1d(s_si, s_ci)
    if not common.size:
        return []
    pos_s = np.searchsorted(s_si, common)
    pos_c = np.searchsorted(s_ci, common)
    mins = np.minimum(s_sv[pos_s], s_cv[pos_c])
    order = np.argsort(-mins)[:top_k]
    terms = [str(t) for t in _FEATURES[common[order]]]
    # cosmetic: drop terms that are substrings of another listed term
    kept = []
    for t in terms:
        if any(t != u and t in u for u in terms):
            continue
        kept.append(t)
    return kept


def _match_reason(src_row, cand_row, base_sim, genre_jaccard):
    """Evidence-based explanation (Phase 3G). Never claims actor/director/period."""
    src_genres = parse_genres(df.loc[src_row, 'genres'])
    cand_genres = parse_genres(df.loc[cand_row, 'genres'])
    shared_genres = [g for g in MULTI_WORD_GENRES or [] if g in src_genres and g in cand_genres] or []
    shared = [g for g in cand_genres if g in src_genres]

    terms = _shared_story_terms(src_row, cand_row)

    searched_title = df.loc[src_row, 'title']

    if terms and shared:
        genre_txt = ", ".join(shared[:3])
        terms_txt = "'" + "', '".join(terms) + "'"
        return (f"Shares genre(s) {genre_txt} and story terms like {terms_txt} "
                f"with {searched_title}.")
    if terms:
        terms_txt = "'" + "', '".join(terms) + "'"
        return f"Overlaps on distinctive story terms like {terms_txt} with {searched_title}."
    if shared:
        genre_txt = ", ".join(shared[:3])
        return f"Shares matching genre(s): {genre_txt} with {searched_title}."
    if float(base_sim) >= 0.25:
        return f"Very strong storyline similarity to {searched_title} based on content analysis."
    return f"Selected for storyline similarity to {searched_title}."


def _match_label(pool_score, score, pool_values):
    """Calibrated relative label: percentile of the rec within the candidate pool.

    Strong Match >= 90th pct, Good Match >= 75th, Similar >= 50th,
    otherwise Moderate Match. Deterministic per query.
    """
    if pool_values is None or not len(pool_values):
        return "Moderate Match"
    rank = 100.0 * (pool_values <= float(score)).mean()
    if rank >= 90.0:
        return "Strong Match"
    if rank >= 75.0:
        return "Good Match"
    if rank >= 50.0:
        return "Similar"
    return "Moderate Match"


def get_recommendations(title, n_recommendations=10, genre_filter=None, mood_filter=None,
                        w_content=None, w_genre=None, w_quality=None, w_pop=None):
    """Hybrid TF-IDF + genre + quality + popularity recommender with MMR rerank.

    Returned items: title, relevance_score, match_label, match_score, reason.
    The selected movie itself is never included (row-exact self-exclusion).

    Optional weight overrides are supported for benchmarking only; production
    uses the module-level constants (W_CONTENT/W_GENRE/W_QUALITY/W_POP).
    """
    if df.empty or tfidf_matrix is None:
        return []

    wc = W_CONTENT if w_content is None else w_content
    wg = W_GENRE if w_genre is None else w_genre
    wq = W_QUALITY if w_quality is None else w_quality
    wp = W_POP if w_pop is None else w_pop

    matched_title = fuzzy_find_movie(title)
    if not matched_title:
        return []

    try:
        row_series = indices[matched_title]
        source_row = int(row_series.iloc[0] if isinstance(row_series, pd.Series) else row_series)
        if source_row < 0 or source_row >= len(df):
            return []
    except (KeyError, IndexError, TypeError):
        return []

    sim_scores = cosine_similarity(tfidf_matrix[source_row:source_row + 1], tfidf_matrix).flatten()
    sim_scores[source_row] = -1.0  # row-exact self-exclusion

    cand_df = pd.DataFrame({
        'row': np.arange(len(df)),
        'title': df['title'],
        'genres': df['genres'].fillna(''),
        'base_sim': sim_scores,
        'quality': df['quality'],
        'norm_popularity': df['norm_popularity'],
        'genres_parsed': df['genres_parsed'],
    })

    # Candidate pool: top-CANDIDATE_POOL by content similarity.
    cand_df = cand_df[cand_df['base_sim'] >= 0.01].nlargest(CANDIDATE_POOL, 'base_sim').copy()

    src_genres = df.loc[source_row, 'genres']

    src_parsed = set(parse_genres(src_genres))

    def genre_sim_row(gs):
        gs = set(gs) if gs else set()
        if not gs or not src_parsed:
            return 0.0
        return len(gs & src_parsed) / len(gs | src_parsed)

    cand_df['genre_sim'] = cand_df['genres_parsed'].apply(genre_sim_row)

    # ------------------------------------------------------------------
    # Hybrid formula (Phase 3D):
    #   score = wc*content + wg*genre_jaccard + wq*quality + wp*pop
    # ------------------------------------------------------------------
    raw = (
        wc * cand_df['base_sim']
        + wg * cand_df['genre_sim']
        + wq * cand_df['quality']
        + wp * cand_df['norm_popularity']
    )

    # Mood override: soft canonical-genre boost (UI feature preserved).
    if mood_filter and mood_filter in MOOD_GENRE_MAP:
        target = [g.lower() for g in MOOD_GENRE_MAP[mood_filter]]
        boost = cand_df['genres_parsed'].apply(
            lambda gs: 0.20 * (sum(1 for g_ in gs if g_.lower() in target) / max(1, len(target)))
        )
        raw = raw + boost

    cand_df['hybrid'] = raw

    # Hard genre filter (canonical).
    if genre_filter:
        if isinstance(genre_filter, str):
            genre_filter = [genre_filter]
        want = {g.lower() for g in genre_filter}
        cand_df = cand_df[cand_df['genres_parsed'].apply(lambda gs: any(g.lower() in want for g in gs))]
        if cand_df.empty:
            return []

    # ------------------------------------------------------------------
    # MMR-style diversity re-ranking (Phase 3F) over the top-MMR_POOL.
    # ------------------------------------------------------------------
    mmr_df = cand_df.nlargest(MMR_POOL, 'hybrid').reset_index(drop=True)
    src_genre_set = src_parsed
    pool_genres = mmr_df['genres_parsed'].tolist()

    def genre_separation(gs, selected):
        """Max Jaccard to any selected row (0 for the first pick)."""
        best = 0.0
        for s in selected:
            j = _jaccard(' '.join(sorted(gs)), ' '.join(sorted(s)))
            if j > best:
                best = j
        return best

    selected_idx = []
    remaining = list(range(len(mmr_df)))
    while remaining and len(selected_idx) < n_recommendations:
        if not selected_idx:
            pick = max(remaining, key=lambda i: mmr_df.loc[i, 'hybrid'])
        else:
            selected_sets = [pool_genres[i] for i in selected_idx]
            def mmr_score(i):
                h = mmr_df.loc[i, 'hybrid']
                div = genre_separation(pool_genres[i], selected_sets)
                return MMR_LAMBDA * h - (1.0 - MMR_LAMBDA) * div
            pick = max(remaining, key=mmr_score)
        selected_idx.append(pick)
        remaining.remove(pick)

    # Calibration pool = full candidate pool (top-300 by content similarity,
    # after any genre filter): percentile is relative to all story-similar
    # candidates, not just the diversified shortlist.
    pool_hybrids = cand_df['hybrid'].to_numpy()

    results = []
    for i in selected_idx:
        row_pos = int(mmr_df.loc[i, 'row'])
        title_i = str(mmr_df.loc[i, 'title'])
        base_sim = float(mmr_df.loc[i, 'base_sim'])
        genre_j = float(mmr_df.loc[i, 'genre_sim'])
        hybrid = float(mmr_df.loc[i, 'hybrid'])

        reason = _match_reason(source_row, row_pos, base_sim, genre_j)
        label = _match_label(None, hybrid, pool_hybrids)
        pct = float((pool_hybrids <= hybrid).mean() * 100.0)

        results.append({
            "title": title_i,
            "relevance_score": round(base_sim, 4),
            "match_label": label,
            "match_score": int(round(pct)),
            "reason": reason,
        })

    return results


if __name__ == "__main__":
    for t in ["The Matrix", "Toy Story", "The Godfather", "Pulp Fiction", "Forrest Gump"]:
        print(f"\n== {t} ==")
        for r in get_recommendations(t, n_recommendations=10):
            print(f"  {r['title']} [{r['match_label']}, {r['match_score']}%] sim={r['relevance_score']} :: {r['reason']}")