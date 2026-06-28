import joblib
import numpy as np
import json
from tensorflow.keras.models import load_model


movie_tower = load_model("new_model/content_based/movie_tower_gelu.keras")

year_scaler = joblib.load("new_model/content_based/year_scaler.pkl")

movie_cols = joblib.load("new_model/content_based/movie_cols.pkl")

GENRE_MAPPING = {
    "Action": "Action",
    "Adventure": "Adventure",
    "Animation": "Animation",
    "Children": "Children",
    "Comedy": "Comedy",
    "Crime": "Crime",
    "Documentary": "Documentary",
    "Drama": "Drama",
    "Fantasy": "Fantasy",
    "Film-Noir": "Film-Noir",
    "Horror": "Horror",
    "Musical": "Musical",
    "Mystery": "Mystery",
    "Romance": "Romance",
    "Science Fiction": "Sci-Fi",
    "Sci-Fi": "Sci-Fi",
    "Thriller": "Thriller",
    "War": "War",
    "Western": "Western",
    "IMAX":"IMAX"
}
def build_movie_vector(movie):

    vector = {col: 0.0 for col in movie_cols}

    genres = movie.genres.split(",")

    for genre in genres:

        genre = genre.strip()

        mapped_col = GENRE_MAPPING.get(genre)

        if mapped_col:
            vector[mapped_col] = 1.0

    year = movie.year if movie.year else 2000
    year_scaled = year_scaler.transform([[year]])[0][0]

    vector["year_scaled"] = float(year_scaled)

    return [vector[col] for col in movie_cols]