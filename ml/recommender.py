import os
import pickle
import difflib
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mood mappings to genres
MOOD_GENRE_MAP = {
    "Uplifting / Feel-Good": ["Comedy", "Family", "Romance", "Animation", "Music"],
    "Intense / Mind-Bending": ["Mystery", "Science", "Fiction", "Sci-Fi", "Thriller", "Crime"],
    "Thrilling / Action-Packed": ["Action", "Adventure", "Fantasy", "War", "Western"],
    "Spooky / Terrifying": ["Horror", "Mystery", "Thriller"],
    "Emotional / Melancholic": ["Drama", "Romance", "History"],
    "Thought-Provoking": ["Documentary", "History", "Science", "Fiction", "Sci-Fi", "Mystery"]
}

@st.cache_resource(show_spinner=False)
def load_models():
    """Loads and caches the massive 45k dataset and TF-IDF matrix once, avoiding startup lag."""
    try:
        df_path = os.path.join(BASE_DIR, 'df.pkl')
        indices_path = os.path.join(BASE_DIR, 'indices.pkl')
        matrix_path = os.path.join(BASE_DIR, 'tfidf_matrix.pkl')

        with open(df_path, 'rb') as f:
            df = pickle.load(f)
        with open(indices_path, 'rb') as f:
            indices = pickle.load(f)
        with open(matrix_path, 'rb') as f:
            tfidf_matrix = pickle.load(f)
            
        # Precompute normalized popularity and vote_average columns for hybrid boosting
        # Fill missing values defensively
        df['popularity'] = pd.to_numeric(df['popularity'], errors='coerce').fillna(0.0)
        df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0.0)
        
        # Max-min scale to 0-1 range
        pop_max = df['popularity'].max()
        pop_min = df['popularity'].min()
        df['norm_popularity'] = (df['popularity'] - pop_min) / (pop_max - pop_min + 1e-8)
        
        # Precompute clean and strict normalized titles for ultra-fast matching (10ms)
        df['title_clean'] = df['title'].fillna('').astype(str).str.lower().str.strip()
        df['title_clean'] = df['title_clean'].str.replace(r'\s*\(\d{4}\)\s*$', '', regex=True)
        df['title_clean'] = df['title_clean'].str.replace(r'[^\w\s]', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
        df['title_strict'] = df['title_clean'].str.replace(r'\s+', '', regex=True)
        
        # Vectorized Roman Numeral Conversion
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
        
        vote_max = df['vote_average'].max()
        vote_min = df['vote_average'].min()
        df['norm_rating'] = (df['vote_average'] - vote_min) / (vote_max - vote_min + 1e-8)
        
        return df, indices, tfidf_matrix
    except Exception as e:
        print(f"Error loading model files: {e}")
        return pd.DataFrame(), pd.Series(), None

# Global access via cached load
df, indices, tfidf_matrix = load_models()

def get_all_movies():
    """Returns a sorted list of all movie titles for selectboxes and dropdown autocomplete."""
    if df.empty:
        return []
    return sorted(df['title'].dropna().unique().tolist())

def get_all_genres():
    """Returns a sorted list of unique genres present in the dataset."""
    if df.empty or 'genres' not in df.columns:
        return []
    
    all_genres = set()
    for genre_str in df['genres'].dropna():
        if isinstance(genre_str, str):
            genres = genre_str.split()
            all_genres.update(genres)
            
    cleaned_genres = {g.capitalize() for g in all_genres if len(g) > 2}
    return sorted(list(cleaned_genres))

def get_moods():
    """Returns the supported interactive psychological mood filters."""
    return list(MOOD_GENRE_MAP.keys())

def fuzzy_find_movie(query_title):
    """
    Finds the exact title in our dataset matching user query.
    Employs exact case-insensitive matches first, cleaned normalized checks, year-aware queries, and fuzzy fallbacks.
    """
    if df.empty or not query_title:
        return None
        
    titles = get_all_movies()
    query_clean = query_title.strip().lower()
    
    # 1. Exact case-insensitive title match
    for title in titles:
        if title.lower().strip() == query_clean:
            return title
            
    # 2. Cleaned normalized title match (removing trailing years and punctuation)
    import re
    query_normalized = re.sub(r'\s*\(\d{4}\)\s*$', '', query_clean) # strip trailing year in parenthesis
    query_normalized = re.sub(r'[^\w\s]', '', query_normalized).strip() # strip punctuation
    
    for title in titles:
        title_clean = title.lower().strip()
        title_normalized = re.sub(r'\s*\(\d{4}\)\s*$', '', title_clean)
        title_normalized = re.sub(r'[^\w\s]', '', title_normalized).strip()
        if title_normalized == query_normalized:
            return title
            
    # 3. Year-aware match
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
                    
    # 4. Substring check
    sub_matches = [title for title in titles if query_clean in title.lower().strip()]
    if sub_matches:
        sub_matches.sort(key=lambda x: abs(len(x) - len(query_title)))
        return sub_matches[0]
        
    # 5. Fuzzy similarity fallback
    fuzzy_matches = difflib.get_close_matches(query_title, titles, n=1, cutoff=0.55)
    if fuzzy_matches:
        return fuzzy_matches[0]
        
    return None

def generate_match_reason(movie_genres, searched_genres, movie_overview, searched_overview, searched_title):
    """Dynamically generates a highly relevant, intelligent content-based explanation for recommendations."""
    # Split genres cleanly
    movie_g_set = set(movie_genres.split()) if isinstance(movie_genres, str) else set(movie_genres)
    searched_g_set = set(searched_genres.split()) if isinstance(searched_genres, str) else set(searched_genres)
    common_genres = list(movie_g_set.intersection(searched_g_set))
    
    mo_lower = str(movie_overview).lower()
    so_lower = str(searched_overview).lower()
    
    themes = []
    if any(w in mo_lower and w in so_lower for w in ["space", "galaxy", "orbit", "astronaut", "wormhole", "dimension", "planet"]):
        themes.append("cosmic exploration elements")
    if any(w in mo_lower and w in so_lower for w in ["killer", "murder", "cop", "detective", "crime", "heist", "theft", "police"]):
        themes.append("gritty crime elements")
    if any(w in mo_lower and w in so_lower for w in ["family", "parent", "home", "father", "mother", "child", "brother", "sister"]):
        themes.append("heartfelt family dynamics")
    if any(w in mo_lower and w in so_lower for w in ["love", "romance", "marry", "marriage", "relationship", "date"]):
        themes.append("romantic story pacing")
    if any(w in mo_lower and w in so_lower for w in ["world", "war", "battle", "soldier", "fight", "save", "army"]):
        themes.append("high-stakes battles")
    if any(w in mo_lower and w in so_lower for w in ["magic", "wizard", "spell", "dragon", "enchanted", "sword", "witch"]):
        themes.append("fantasy narrative arcs")
        
    if themes:
        primary_theme = themes[0]
        if common_genres:
            return f"Aligns with the '{common_genres[0]}' pacing and shares {primary_theme} with {searched_title}."
        return f"Aligns with the {primary_theme} and structural storytelling of {searched_title}."
        
    if common_genres:
        return f"Shares matching '{common_genres[0]}' attributes and story flow with {searched_title}."
        
    return f"Shares narrative themes and high storyline similarity with {searched_title}."

def get_recommendations(title, n_recommendations=10, genre_filter=None, mood_filter=None):
    """
    Computes recommendations using an advanced hybrid TF-IDF + Cosine Similarity scoring engine.
    Applies the hybrid rating, popularity, and mood-boosting algorithms exclusively to the top 100
    storyline-similar set to guarantee high recommendations relevance.
    """
    if df.empty or tfidf_matrix is None:
        return []
        
    # Find matching title using robust fuzzy lookup
    matched_title = fuzzy_find_movie(title)
    if not matched_title:
        return []
        
    try:
        # Get index mapped to matched title
        idx = indices[matched_title]
        
        # Resolve series matching duplicate titles if any
        if isinstance(idx, pd.Series):
            idx = idx.iloc[0]
            
        # Compute base cosine similarity score against all movies
        sim_scores = cosine_similarity(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()
        
        # Make a copy of dataframe indices and base similarity
        scores_df = pd.DataFrame({
            'index': np.arange(len(df)),
            'title': df['title'],
            'genres': df['genres'].fillna(''),
            'base_sim': sim_scores,
            'norm_popularity': df['norm_popularity'],
            'norm_rating': df['norm_rating']
        })
        
        # Filter out the searched movie itself
        scores_df = scores_df[scores_df['title'].str.lower() != matched_title.lower()]
        
        # --- TOP 100 STORYLINE SIMILAR FILTER (HIGH RELEVANCE GUARANTEE) ---
        top_similar_df = scores_df.sort_values(by='base_sim', ascending=False).head(100).copy()
        
        # --- HYBRID SCORING CALCULATION (ONLY ON THE TOP 100) ---
        # Formula: Combined Score = 0.70*BaseSim + 0.15*Popularity + 0.15*Rating
        top_similar_df['hybrid_score'] = (
            0.70 * top_similar_df['base_sim'] +
            0.15 * top_similar_df['norm_popularity'] +
            0.15 * top_similar_df['norm_rating']
        )
        
        # --- MOOD AFFECTED BOOSTING ---
        if mood_filter and mood_filter in MOOD_GENRE_MAP:
            target_genres = MOOD_GENRE_MAP[mood_filter]
            
            def calculate_mood_boost(genres_str):
                genres_lower = genres_str.lower()
                matches = sum(1 for g in target_genres if g.lower() in genres_lower)
                return 0.20 * (matches / max(1, len(target_genres)))
                
            top_similar_df['mood_boost'] = top_similar_df['genres'].apply(calculate_mood_boost)
            top_similar_df['hybrid_score'] += top_similar_df['mood_boost']
            
        # --- GENRE FILTERING (HARD FILTER) ---
        if genre_filter:
            if isinstance(genre_filter, str):
                genre_filter = [genre_filter]
                
            def matches_genre(genres_str):
                genres_lower = genres_str.lower()
                return any(g.lower() in genres_lower for g in genre_filter)
                
            top_similar_df = top_similar_df[top_similar_df['genres'].apply(matches_genre)]
            
        # Sort by final hybrid score
        top_matches = top_similar_df.sort_values(by='hybrid_score', ascending=False).head(n_recommendations)
        
        # Build dynamic AI-explanation response packages
        results = []
        searched_row = df[df['title'] == matched_title].iloc[0]
        searched_genres = searched_row.get('genres', '')
        searched_overview = searched_row.get('overview', '')
        
        for _, row in top_matches.iterrows():
            movie_title = row['title']
            relevance = row['base_sim']
            
            # Generate personalized alignment description
            reason = generate_match_reason(
                row['genres'], searched_genres,
                df[df['title'] == movie_title].iloc[0].get('overview', ''),
                searched_overview, matched_title
            )
            
            results.append({
                "title": movie_title,
                "relevance_score": relevance,
                "reason": reason
            })
            
        return results
        
    except Exception as e:
        print(f"Error in recommendation logic: {e}")
        return []
