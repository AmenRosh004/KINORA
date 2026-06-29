import requests
from config import TMDB_API_KEY

genre_mapping = {
        "Science Fiction": "Sci-Fi",
        "Sci-Fi": "Sci-Fi",
        "Action": "Action",
        "Adventure": "Adventure",
        "Animation": "Animation",
        "Comedy": "Comedy",
        "Crime": "Crime",
        "Documentary": "Documentary",
        "Drama": "Drama",
        "Fantasy": "Fantasy",
        "Horror": "Horror",
        "Musical": "Musical",
        "Mystery": "Mystery",
        "Romance": "Romance",
        "Thriller": "Thriller",
        "War": "War",
        "Western": "Western",
        "Children":"Children",
        "IMAX": "IMAX"
        }
    

def get_movie_details(movie_id):
    try:
        url = (
            f"https://api.themoviedb.org/3/movie/"
            f"{movie_id}?api_key={TMDB_API_KEY}"
        )
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"TMDB Error: {e}")
        return {}
        

def get_movie_credits(movie_id):
    try:
        url = (
            f"https://api.themoviedb.org/3/movie/"
            f"{movie_id}/credits?api_key={TMDB_API_KEY}"
        )
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"TMDB Error: {e}")
        return {}



def get_popular_movies():
    try:
        url = (
            f"https://api.themoviedb.org/3/movie/popular"
            f"?api_key={TMDB_API_KEY}"
        )
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"TMDB Error: {e}")
        return {"results": []}


def search_movies(query):
    try:
        url = (
            f"https://api.themoviedb.org/3/search/movie"
            f"?api_key={TMDB_API_KEY}&query={query}"
        )
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"TMDB Error: {e}")
        return {"results": []}