from flask import Flask,render_template,request,redirect,session
import requests
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_bcrypt import Bcrypt
import pickle,joblib
import numpy as np
from tensorflow.keras.models import load_model
import json
from movie_utils import build_movie_vector
from app import app, db, User, Rating
def update_user_embedding(user_id):
    rating_count=Rating.query.filter_by(user_id=user_id).count()
    if rating_count > 5:
        user_vec = build_user_vector(user_id)
    else:
        user_vec = build_preference_vector(user_id)
    
    xu = np.array([user_vec], dtype=np.float32)
    vu = user_tower.predict(xu, verbose=0)[0]
    norm = np.linalg.norm(vu)

    if norm != 0:
        vu = vu / norm
        
    user = User.query.get(user_id)
    user.embedding = json.dumps(vu.tolist())
    db.session.commit()

with app.app_context():

    users = User.query.all()

    for user in users:
        update_user_embedding(user.id)

    print("Done")