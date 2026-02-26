import pickle
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_pkl(filename):
    """Utility to securely load pickle files."""
    path = os.path.join(BASE_DIR, filename)
    with open(path, 'rb') as f:
        return pickle.load(f)

# Load data at startup
try:
    df = load_pkl('df.pkl')
    indices = load_pkl('indices.pkl')
    # tfidf = load_pkl('tfidf.pkl') # TFIDF vectorizer not strictly needed if we already have the matrix
    tfidf_matrix = load_pkl('tfidf_matrix.pkl')
except Exception as e:
    print(f"Error loading pickle files: {e}")
    df = pd.DataFrame()
    indices = pd.Series()
    tfidf_matrix = None

def get_all_movies():
    """Returns a list of all movie titles for the dropdown."""
    if df.empty:
        return []
    return df['title'].tolist()

def get_all_genres():
    """Returns a sorted list of all unique genres in the dataset."""
    if df.empty or 'genres' not in df.columns:
        return []
    
    # Genres are likely space-separated strings like "Action Adventure"
    all_genres = set()
    for genre_str in df['genres'].dropna():
        # Split by space and add to set
        if isinstance(genre_str, str):
            genres = genre_str.split()
            all_genres.update(genres)
            
    return sorted(list(all_genres))

def get_recommendations(title, n_recommendations=5, genre_filter=None):
    """
    Computes TF-IDF cosine similarity for a given movie title
    and returns a list of top N similar movie titles, optionally
    filtered by a list of genres.
    """
    if df.empty or tfidf_matrix is None:
        return []

    # Find lowercase match to be robust
    matches = df[df['title'].str.lower() == title.lower()]
    
    if matches.empty:
        return []
        
    # Get the index of the movie that matches the title
    # We use the index from the DataFrame to access tfidf_matrix
    try:
        idx_match = indices[matches.iloc[0]['title']]
        
        if isinstance(idx_match, pd.Series):
            idx = idx_match.iloc[0]
        else:
            idx = idx_match
            
        # Compute cosine similarity
        sim_scores = cosine_similarity(tfidf_matrix[idx:idx+1], tfidf_matrix).flatten()
        
        # We need to fetch more indices if we're filtering, otherwise just n_recommendations
        fetch_count = len(df) if genre_filter else n_recommendations + 1
        top_indices = sim_scores.argsort()[::-1][1:fetch_count] # skip the exact match itself
        
        # Get list of recommended movie titles
        recommended_movies = []
        for i in top_indices:
            movie_row = df.iloc[i]
            
            if genre_filter:
                movie_genres_str = str(movie_row.get('genres', ''))
                # Check if ANY of the selected genres are in the movie's genre string
                if not any(g.lower() in movie_genres_str.lower() for g in genre_filter):
                    continue
                    
            recommended_movies.append(movie_row['title'])
            
            if len(recommended_movies) == n_recommendations:
                break
                
        return recommended_movies
        
    except Exception as e:
        print(f"Error generating recommendations for '{title}': {e}")
        return []
