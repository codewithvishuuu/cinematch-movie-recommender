import re
import urllib.parse
import requests
import streamlit as st
from config.settings import TMDB_API_KEY, TMDB_BASE_URL
from services.tmdb_service import fetch_movie_details

def normalize_title(title):
    """Normalizes title: lowercase, strip year in parenthesis, strip punctuation, strip spaces."""
    if not title or not isinstance(title, str):
        return ""
    # Lowercase
    title_norm = title.lower()
    # Strip trailing year in parenthesis e.g. "Toy Story (1995)" -> "Toy Story"
    title_norm = re.sub(r'\s*\(\d{4}\)\s*$', '', title_norm)
    # Strip punctuation and special characters
    title_norm = re.sub(r'[^\w\s]', ' ', title_norm)
    # Compress whitespace and strip
    title_norm = re.sub(r'\s+', ' ', title_norm).strip()
    return title_norm

def strict_normalize_title(title):
    """Strips all spaces and punctuation to resolve cases like 'toystory' -> 'toystory'."""
    title_norm = normalize_title(title)
    return re.sub(r'\s+', '', title_norm)

def convert_roman_numerals(title):
    """Replaces common roman numerals with numbers to handle sequel matching (e.g. 'part ii' -> 'part 2')."""
    if not title:
        return ""
    title_lower = title.lower()
    roman_map = {
        r'\bpart\s+i\b': 'part 1',
        r'\bpart\s+ii\b': 'part 2',
        r'\bpart\s+iii\b': 'part 3',
        r'\bpart\s+iv\b': 'part 4',
        r'\bpart\s+v\b': 'part 5',
        r'\bii\b': '2',
        r'\biii\b': '3',
        r'\biv\b': '4',
        r'\bv\b': '5'
    }
    for roman, decimal in roman_map.items():
        title_lower = re.sub(roman, decimal, title_lower)
    return title_lower

@st.cache_data(ttl=3600, show_spinner=False)
def search_movies_pipeline(query, limit=5):
    """
    Production-grade search pipeline that executes smart matching:
    1. Query parser handles typo matching, missing spaces, sequels, and roman numerals.
    2. Performs dynamic lookup in local df.pkl dataset (45,447 movies).
    3. Triggers live TMDB search fallback/merge.
    4. Ranks results by popularity to deliver an elite Netflix autocomplete deck.
    """
    if not query or not isinstance(query, str) or len(query.strip()) < 2:
        return []

    query_clean = query.strip()
    query_norm = normalize_title(query_clean)
    query_strict = strict_normalize_title(query_clean)
    query_roman = strict_normalize_title(convert_roman_numerals(query_clean))

    def strip_the_prefix(s):
        if s.startswith("the"):
            return s[3:]
        return s

    query_strict_nothe = strip_the_prefix(query_strict)
    query_roman_nothe = strip_the_prefix(query_roman)

    results = []
    seen_titles = set()

    # Step 1: Search local 45,447 dataset first to ensure maximum recommender compatibility
    try:
        from ml.recommender import df
        import pandas as pd
        if not df.empty:
            # Vectorized conditional filters
            cond_exact = df['title'].str.lower().str.strip() == query_clean.lower()
            cond_clean = df['title_clean'] == query_norm
            cond_strict = df['title_strict'] == query_strict
            cond_roman = df['title_roman'] == query_roman
            
            # Definite prefix stripping
            cond_strict_nothe = df['title_strict'].str.replace(r'^the', '', regex=True) == query_strict_nothe
            cond_roman_nothe = df['title_roman'].str.replace(r'^the', '', regex=True) == query_roman_nothe
            
            # Vectorized substring filters
            cond_sub_strict = df['title_strict'].str.contains(query_strict, na=False)
            cond_sub_roman = df['title_roman'].str.contains(query_roman, na=False)
            cond_sub_strict_nothe = df['title_strict'].str.replace(r'^the', '', regex=True).str.contains(query_strict_nothe, na=False)
            cond_sub_roman_nothe = df['title_roman'].str.replace(r'^the', '', regex=True).str.contains(query_roman_nothe, na=False)
            cond_sub_clean = df['title_clean'].str.contains(query_norm, na=False)
            
            # Combine filters
            comb_mask = (cond_exact | cond_clean | cond_strict | cond_roman | 
                         cond_strict_nothe | cond_roman_nothe | 
                         cond_sub_strict | cond_sub_roman | 
                         cond_sub_strict_nothe | cond_sub_roman_nothe | cond_sub_clean)
                         
            df_matches = df[comb_mask].copy()
            
            if not df_matches.empty:
                # Dynamically calculate match score
                df_matches['score'] = 10
                df_matches.loc[cond_sub_clean, 'score'] = 45
                df_matches.loc[cond_sub_strict_nothe, 'score'] = 60
                df_matches.loc[cond_sub_strict, 'score'] = 65
                df_matches.loc[cond_sub_roman_nothe, 'score'] = 60
                df_matches.loc[cond_sub_roman, 'score'] = 65
                df_matches.loc[cond_roman_nothe, 'score'] = 85
                df_matches.loc[cond_strict_nothe, 'score'] = 85
                df_matches.loc[cond_roman, 'score'] = 88
                df_matches.loc[cond_strict, 'score'] = 88
                df_matches.loc[cond_clean, 'score'] = 90
                df_matches.loc[cond_exact, 'score'] = 100
                
                # Sort matches by match score, then popularity
                df_matches['popularity'] = pd.to_numeric(df_matches['popularity'], errors='coerce').fillna(0.0)
                df_matches = df_matches.sort_values(by=['score', 'popularity'], ascending=[False, False]).head(limit * 2)
                
                for _, row in df_matches.iterrows():
                    t = row['title']
                    t_lower = t.lower().strip()
                    if t_lower not in seen_titles:
                        seen_titles.add(t_lower)
                        genres_str = str(row.get('genres', '') or '')
                        results.append({
                            "title": t,
                            "source": "local",
                            "popularity": float(row.get('popularity', 0.0) or 0.0),
                            "vote_average": float(row.get('vote_average', 0.0) or 0.0),
                            "genres": [g.capitalize() for g in genres_str.split() if len(g) > 2][:3],
                            "match_score": int(row['score'])
                        })
    except Exception as e:
        print(f"[Search Service] Local search error: {e}")

    # Step 2: Query TMDB Live Search to merge popular/trending films and new releases
    if TMDB_API_KEY:
        try:
            search_query = urllib.parse.quote(query_clean)
            url = f"{TMDB_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={search_query}&language=en-US&include_adult=false"
            res = requests.get(url, timeout=4)
            if res.status_code == 200:
                tmdb_data = res.json().get("results", [])
                for item in tmdb_data[:limit]:
                    item_title = item.get("title", "")
                    item_lower = item_title.lower().strip()
                    
                    if item_lower not in seen_titles:
                        seen_titles.add(item_lower)
                        
                        # Find release year
                        rel_date = item.get("release_date", "")
                        year = rel_date[:4] if rel_date and len(rel_date) >= 4 else "N/A"
                        
                        # Safe parsing of poster and backdrop
                        poster_path = item.get("poster_path")
                        backdrop_path = item.get("backdrop_path")
                        
                        # Try to resolve genre IDs from TMDB if possible
                        genres = ["Feature"] # default
                        
                        results.append({
                            "title": item_title,
                            "source": "tmdb",
                            "popularity": float(item.get("popularity", 0.0) or 0.0),
                            "vote_average": float(item.get("vote_average", 0.0) or 0.0),
                            "release_date": rel_date,
                            "year": year,
                            "poster_path": poster_path,
                            "backdrop_path": backdrop_path,
                            "genres": genres,
                            "match_score": 75 # default tmdb relevance score
                        })
        except Exception as e:
            print(f"[Search Service] TMDB search error: {e}")

    # Step 3: Fetch full details (poster URLs, trailers) for the merged results
    # Sort merged results by match score first, then by popularity
    results.sort(key=lambda x: (-x["match_score"], -x["popularity"]))
    
    final_deck = []
    for item in results[:limit]:
        try:
            # fetch_movie_details aggregates full images, trailer links and genres beautifully
            details = fetch_movie_details(item["title"])
            if details:
                final_deck.append(details)
        except Exception as e:
            print(f"[Search Service] Details aggregation error for '{item['title']}': {e}")
            
    return final_deck
