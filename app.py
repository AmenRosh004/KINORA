from flask import Flask,render_template,request,redirect,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_bcrypt import Bcrypt
import numpy as np
import json
from movie_utils import build_movie_vector
from config import (SECRET_KEY,DATABASE_URL,TMDB_API_KEY,user_cols,movie_cols,year_scaler,rating_scaler,user_tower,movie_tower)
from services.tmdb import (genre_mapping,get_movie_details,get_movie_credits,get_popular_movies,search_movies)
app=Flask(__name__)
api_key = TMDB_API_KEY
app.secret_key = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    age=db.Column(db.Integer)
    occupation=db.Column(db.Integer)
    gender=db.Column(db.String(20))
    favorite_genres=db.Column(db.Text)
    disliked_genres=db.Column(db.Text)
    embedding=db.Column(db.Text)
class Rating(db.Model):

    id = db.Column(db.Integer,primary_key=True)

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

    movie_id = db.Column(db.Integer,nullable=False)

    rating = db.Column(db.Integer,nullable=False)

class UserGenrePreference(db.Model):
    id=db.Column(db.Integer,primary_key=True)

    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

    genre = db.Column(db.String(50),nullable=False)

    score = db.Column(db.Integer,nullable=False)

class Movie(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(255),nullable=False)
    genres = db.Column(db.String(255),nullable=False)
    year=db.Column(db.Integer)
    embedding = db.Column(db.Text)
    poster_url=db.Column(db.Text)
    backdrop_url=db.Column(db.Text)


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

@app.route("/",methods=["GET","POST"])
def home():
    
    #print(session)
    is_search=False
    #url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}"
    if request.method=="POST":
        movie_name=request.form.get("movie","").strip()

        if movie_name:
            is_search=True
            data=search_movies(movie_name)
        else:
            data=get_popular_movies()  
    else:
        data=get_popular_movies()
    movies = []

    for m in data["results"][:20]:
        if m["poster_path"] and m["backdrop_path"]:
            movies.append({
                "id": m["id"],
                "title": m["title"],
                "poster": "https://image.tmdb.org/t/p/w500" + m["poster_path"],
                "backdrop": "https://image.tmdb.org/t/p/original" + m["backdrop_path"]
            })
    recommended = []   
    hero_movies=[]
    more_recommendations=[] 
    if session.get("user_id"):

        recommended = get_recommendation(session["user_id"])
        hero_movies=recommended[:5]
        more_recommendations=recommended[5:]
    else:
        guest_movies = (Movie.query.filter(Movie.backdrop_url.isnot(None)).limit(4).all())
        hero_movies = []

        for m in guest_movies:
            hero_movies.append({
                "id": m.id,
                "title": m.title,
                "poster": m.poster_url,
                "backdrop": m.backdrop_url,
                "genres": m.genres
            })
            
    action_movies=(Movie.query.filter(Movie.genres.ilike("%Action%")).limit(20).all())
    scifi_movies=(Movie.query.filter(Movie.genres.ilike("%Science Fiction%")).limit(20).all())
    comedy_movies=(Movie.query.filter(Movie.genres.ilike("%Comedy%")).limit(20).all())
    rom_drama_movies=(Movie.query.filter(and_(Movie.genres.ilike('%Romance%'),Movie.genres.ilike('%Drama%'))).limit(20).all()) 
    return render_template("index.html",
                            movies=movies,
                            hero_movies=hero_movies,
                            more_recommendations=more_recommendations,
                            is_search=is_search,
                            action_movies=action_movies,
                            scifi_movies=scifi_movies,
                            comedy_movies=comedy_movies,
                            rom_drama_movies=rom_drama_movies)

@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    data=get_movie_details(movie_id)
    credit_data = get_movie_credits(movie_id)
    director="Not Available"
    for person in credit_data.get("crew",[]):
        if person["job"]=="Director":
            director=person["name"]
            break
    cast=[]
    for actor in credit_data.get("cast",[])[:18]:
        if actor["profile_path"]:
            cast.append(actor)
    db_movie=Movie.query.get(movie_id)
    similar_movies=[]
    if db_movie and db_movie.embedding:
        curr_embedding=np.array(json.loads(db_movie.embedding),dtype=np.float32)
        all_movies=Movie.query.filter(Movie.embedding.isnot(None),Movie.id!=movie_id).all()
        for m in all_movies:
            emb=np.array(json.loads(m.embedding),dtype=np.float32)
            similarity=float(np.dot(curr_embedding,emb))
            similar_movies.append((similarity,m))
        similar_movies.sort(key=lambda x:x[0],reverse=True)
        similar_movies=[movie for similarity,movie in similar_movies[:10]]


    return render_template("details.html",movie=data,director=director,cast=cast,similar_movies=similar_movies)

@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        user=User.query.filter_by(username=username).first()
        
        if user:
            if bcrypt.check_password_hash(user.password,password):
                session['user_id']=user.id
                session['username']=user.username  
                return redirect("/")
            else:
                return render_template('login.html',error='Incorrect Password')
        else:
            return render_template('login.html',error='User not found')
    return render_template("login.html")

@app.route("/register",methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        age=request.form['age']
        gender=request.form['gender']
        occupation=request.form['occupation']
        password=request.form['password']
        confirm_password=request.form['confirm_password']
        fav_genres=request.form.getlist('favorite_genres')
        dislike_genres = request.form.getlist("disliked_genres")
        if password != confirm_password:
            return render_template("register.html",error="Passwords do not match")
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("register.html",error="Username already exists")
        
        existing_email=User.query.filter_by(email=email).first()
        if existing_email:
            return render_template("register.html",error='Email already exists')
    
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username,email=email,password=hashed_password,age=age,occupation=occupation,gender=gender)
        new_user.favorite_genres = json.dumps(fav_genres)
        new_user.disliked_genres = json.dumps(dislike_genres)
        db.session.add(new_user)
        db.session.commit()
        update_user_embedding(new_user.id)
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        return redirect('/')
    return render_template("register.html")

with app.app_context():
    db.create_all()

@app.route("/profile")
def profile():

    if not session.get("user_id"):
        return redirect("/login")

    user = User.query.get(session["user_id"])
    occupation_map = {
        0:'Other',
        1:'Academic / Educator',
        2:'Artist',
        3:'Clerical / Admin',
        4:'College / Grad Student',
        5:'Customer Service',
        6:'Doctor / Health Care',
        7:'Executive / Managerial',
        8:'Farmer',
        9:'Homemaker',
        10:'K-12 Student',
        11:'Lawyer',
        12:'Programmer',
        13:'Retired',
        14:'Sales / Marketing',
        15:'Scientist',
        16:'Self-Employed',
        17:'Technician / Engineer',
        18:'Tradesman / Craftsman',
        19:'Unemployed',
        20:'Writer'
    }
    occupation_text = occupation_map[user.occupation]
    return render_template("profile.html",user=user,occupation_text=occupation_text)

@app.route("/preference-test",methods=['GET','POST'])
def preference_test():
    if not session.get("user_id"):
        return redirect("/login")
    genres = ["Action","Adventure","Comedy","Drama","Fantasy","Horror","Romance","Sci-Fi","Thriller"]
    
    if request.method == "POST":

        user_id = session["user_id"]

        # remove old preferences
        UserGenrePreference.query.filter_by(user_id=user_id).delete()

        for genre in genres:

            score = int(request.form.get(genre, 0))

            pref = UserGenrePreference(user_id=user_id,genre=genre,score=score)

            db.session.add(pref)

        db.session.commit()

        return redirect("/profile")

    return render_template("preference_test.html",genres=genres)    

@app.route('/rate',methods=['POST'])
def rate():
    if not session.get('user_id'):
        return redirect('/login')

    movie_id=request.form['movie_id']
    rating=request.form['rating']

    movie = Movie.query.get(movie_id)
    if not movie:

        data = get_movie_details(movie_id)

        genre_names = []
        for genre in data.get("genres",[]):
            genre_names.append(genre["name"])

        genres_string = ",".join(genre_names)
        release_year=None
        if data.get('release_date'):
            release_year=int(data['release_date'][:4])
        #poster and backdrop adding for searched movies
        poster_url=None
        backdrop_url=None
        if data.get("poster_path"):
            poster_url = ("https://image.tmdb.org/t/p/w500"+ data["poster_path"])

        if data.get("backdrop_path"):
            backdrop_url = ("https://image.tmdb.org/t/p/original"+ data["backdrop_path"])
        movie = Movie(id=data["id"],title=data["title"],genres=genres_string,year=release_year,poster_url=poster_url,backdrop_url=backdrop_url)
        movie_vec = build_movie_vector(movie)
        xm = np.array([movie_vec], dtype=np.float32)
        vm = movie_tower.predict(xm, verbose=0)[0]
        norm=np.linalg.norm(vm)
        if norm!=0:
            vm=vm/norm
        movie.embedding = json.dumps(vm.tolist())
        db.session.add(movie)
    
    #rating logic
    existing_rating=Rating.query.filter_by(user_id=session['user_id'],movie_id=movie_id).first()
    if existing_rating:
        existing_rating.rating=rating
    else:
        new_rating=Rating(user_id=session['user_id'],movie_id=movie_id,rating=rating)
        db.session.add(new_rating)
    db.session.commit()

    update_user_embedding(session["user_id"])
    return redirect(f"/movie/{movie_id}")

@app.route('/user-vector')
def user_vector():
    if not session.get('user_id'):
        return redirect('/login')
    ratings=Rating.query.filter_by(user_id=session['user_id']).all()
    genre_vector={}
    rating_sum=0
    for r in ratings:
        rating_sum+=int(r.rating)
        movie=Movie.query.get(r.movie_id)
        if not movie:
            continue
        genres=movie.genres.split(',')
        for g in genres:
            if g not in genre_vector:
                genre_vector[g]=0
            genre_vector[g]+=int(r.rating)
    
    if rating_sum == 0:
        return "No ratings found"
    for genre in genre_vector:
        genre_vector[genre] = round(genre_vector[genre] / rating_sum,3)
    
    return str(genre_vector)
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

if __name__== "__main__":
    app.run(debug=True)
