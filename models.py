from database import db

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


class Movie(db.Model):
    id = db.Column(db.Integer,primary_key=True)

    title = db.Column(db.String(255),nullable=False)

    genres = db.Column(db.String(255),nullable=False)

    year=db.Column(db.Integer)

    embedding = db.Column(db.Text)

    poster_url=db.Column(db.Text)

    backdrop_url=db.Column(db.Text)