from flask import Flask,render_template,request,redirect,session
from sqlalchemy import and_
from database import db
from flask_bcrypt import Bcrypt
import numpy as np
import json
from movie_utils import build_movie_vector
from config import (SECRET_KEY,DATABASE_URL,TMDB_API_KEY,user_cols,movie_cols,year_scaler,rating_scaler,user_tower,movie_tower)
from services.tmdb import (genre_mapping,get_movie_details,get_movie_credits,get_popular_movies,search_movies)
from models import User, Movie, Rating
from services.recommender import (update_user_embedding,build_preference_vector,build_user_vector,get_recommendation,)

app=Flask(__name__)
api_key = TMDB_API_KEY
app.secret_key = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
bcrypt = Bcrypt(app)



@app.route("/",methods=["GET","POST"])
def home():
    
    is_search=False
    search_query = ""
    if request.method=="POST":
        
        movie_name=request.form.get("movie","").strip()

        if movie_name:
            is_search=True
            search_query = movie_name
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
                            search_query=search_query,
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
    for actor in credit_data.get("cast",[]):
        if actor.get("profile_path"):
            cast.append(actor)
        if len(cast)==16:
            break
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
