import json
import numpy as np

from database import db
from models import User, Movie, Rating

from config import (user_cols,rating_scaler,user_tower,)

from services.tmdb import genre_mapping

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
    
def build_preference_vector(user_id):
    user=User.query.get(user_id)
    favorite_genres = json.loads(user.favorite_genres or "[]")
    disliked_genres = json.loads(user.disliked_genres or "[]")
    genre_cols=user_cols[:-2]
    weighted_sum=0

    genre_scores={g:0.0 for g in genre_cols}

    #favorite
    for genre in favorite_genres:
        mapped=genre_mapping.get(genre)
        if mapped in genre_scores:
            genre_scores[mapped]+=1
            weighted_sum+=1
        
    #disliked
    for genre in disliked_genres:
        mapped=genre_mapping.get(genre)
        if mapped in genre_scores:
            genre_scores[mapped]-=1
            weighted_sum+=1
    
    #normalise
    if weighted_sum>0:
        for g in genre_scores:
            genre_scores[g]/=weighted_sum

    #vector building
    user_vec=[]
    for col in genre_cols:
        user_vec.append(genre_scores[col])


    # no ratings yet
    scaled_stats = rating_scaler.transform([[0, 0]])

    avg_rating_scaled = float(scaled_stats[0][0])
    rating_count_scaled = float(scaled_stats[0][1])

    user_vec.append(avg_rating_scaled)
    user_vec.append(rating_count_scaled)

    return user_vec


def build_user_vector(user_id):
    ratings=Rating.query.filter_by(user_id=user_id).all()
    rating_count=len(ratings)
    if rating_count>0:
        avg_rating=sum(int(r.rating) for r in ratings)/rating_count
    else:
        avg_rating=0
    
    rating_weight = {
        1: -1.5,
        2: -0.5,
        3: 0.5,
        4: 1.5,
        5: 2.5
    }
    genre_cols = user_cols[:-2]
    genre_scores = {g: 0.0 for g in genre_cols}
    weight_sum=0.0
    for r in ratings:
        movie=Movie.query.get(r.movie_id)
        if not movie:
            continue
        weight=rating_weight[int(r.rating)]
        weight_sum+=abs(weight)

        genres=movie.genres.split(",")
        for g in genres:
            g=g.strip()
            mapped=genre_mapping.get(g)
            if mapped in genre_scores:
                genre_scores[mapped]+=weight
    if weight_sum>0:
        for g in genre_scores:
            genre_scores[g]/=weight_sum
    
    #bulding vector
    user_vec=[]
    for col in genre_cols:
        user_vec.append(float(genre_scores[col]))
    

    #ratings
    scaled_stats=rating_scaler.transform([[avg_rating,rating_count]])
    avg_rating_scaled = float(scaled_stats[0][0])
    rating_count_scaled = float(scaled_stats[0][1])

    user_vec.append(avg_rating_scaled)
    user_vec.append(rating_count_scaled)
    return user_vec


def get_recommendation(user_id,limit=20):
    user=User.query.get(user_id)
    if not user or not user.embedding:
        return []
    vu=np.array(json.loads(user.embedding),dtype=np.float32)

    recommendation=[]
    rated_ids={r.movie_id for r in Rating.query.filter_by(user_id=user_id).all()}
    movies=Movie.query.all()

    for movie in movies:
        if not movie.embedding:
            continue
        if movie.id in rated_ids:
            continue
        vm=np.array(json.loads(movie.embedding),dtype=np.float32)
        score=float(np.dot(vu,vm))
        recommendation.append((movie,score))
        
    recommendation.sort(key=lambda x:x[1],reverse=True)
    top=recommendation[:limit]
    final=[]
    for movie,score in top:
        final.append({
            'id':movie.id,
            'title':movie.title,
            'poster':movie.poster_url,
            'backdrop':movie.backdrop_url,
            'genres':movie.genres,
            'score':score
        })

    return final