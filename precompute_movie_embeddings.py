import joblib
import numpy as np
import json
from tensorflow.keras.models import load_model
from movie_utils import build_movie_vector
from app import app, db, Movie

movie_tower = load_model("new_model/content_based/movie_tower_gelu.keras")

year_scaler = joblib.load("new_model/content_based/year_scaler.pkl")

movie_cols = joblib.load("new_model/content_based/movie_cols.pkl")



with app.app_context():

    movies = Movie.query.filter(Movie.embedding.is_(None)).all()
    for movie in movies:
        movie_vec=build_movie_vector(movie)
        xm=np.array([movie_vec],dtype=np.float32)

        vm=movie_tower.predict(xm,verbose=0)[0]
        norm=np.linalg.norm(vm)
        if norm!=0:
            vm=vm/norm
        movie.embedding=json.dumps(vm.tolist())
    db.session.commit()
    print('done')
    
    