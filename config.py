import os
import pickle
import joblib
from dotenv import load_dotenv
from tensorflow.keras.models import load_model

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

with open("new_model/content_based/user_cols.pkl", "rb") as f:
    user_cols = pickle.load(f)

with open("new_model/content_based/movie_cols.pkl", "rb") as f:
    movie_cols = pickle.load(f)

year_scaler = joblib.load("new_model/content_based/year_scaler.pkl")
rating_scaler = joblib.load("new_model/content_based/user_scaler.pkl")

user_tower = load_model("new_model/content_based/user_tower_gelu.keras")
movie_tower = load_model("new_model/content_based/movie_tower_gelu.keras")
