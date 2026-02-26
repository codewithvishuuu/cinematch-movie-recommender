import os
import requests
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"

def get_fallback_details(title):
    """Fallback details if API key is missing or movie not found."""
    return {
        "title": title,
        "poster_url": "https://via.placeholder.com/500x750?text=Poster+Not+Found",
        "rating": "N/A",
        "overview": "No plot available or API key is missing.",
        "release_date": "N/A"
    }

def fetch_movie_details(title):
    """Fetches full movie details including poster, rating, and plot using title search from OMDb API."""
    if not OMDB_API_KEY or OMDB_API_KEY == "PLEASE_ENTER_YOUR_API_KEY_HERE":
        return get_fallback_details(title)
        
    query = urllib.parse.quote(title)
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={query}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(data)
        
        if data.get("Response") == "False":
            return None
            
        poster_url = data["Poster"]
        if poster_url == "N/A" or not poster_url:
            poster_url = "https://via.placeholder.com/500x750?text=No+Poster"
            
        return {
            "title": data.get("Title", title),
            "poster_url": poster_url,
            "rating": data["imdbRating"],
            "overview": data["Plot"],
            "release_date": data["Year"]
        }
    except Exception as e:
        print(f"Error fetching movie {title}: {e}")
        return None

def get_popular_movies():
    """Returns a static list of popular movies since OMDb API doesn't have a trending endpoint."""
    popular_titles = [
        "Inception", "The Dark Knight", "Interstellar", "Avatar", 
        "The Avengers", "Titanic", "The Matrix", "Gladiator",
        "The Godfather", "Pulp Fiction", "Forrest Gump", "The Shawshank Redemption"
    ]
    
    popular_movies = []
    for title in popular_titles:
        details = fetch_movie_details(title)
        popular_movies.append(details)
        
    return popular_movies
