import requests

from app import app, db, Movie, api_key

genreids_map = {
    28: 'Action',
    12: 'Adventure',
    16: 'Animation',
    35: 'Comedy',
    80: 'Crime',
    99: 'Documentary',
    18: 'Drama',
    10751: 'Children',
    14: 'Fantasy',
    27: 'Horror',
    10402: 'Musical',
    9648: 'Mystery',
    10749: 'Romance',
    878: 'Science Fiction',
    53: 'Thriller',
    10752: 'War',
    37: 'Western'
}

with app.app_context():

    added = 0
    updated=0  

    endpoints = [
        "popular",
        "top_rated"
    ]

    for endpoint in endpoints:

        print(f"\nFetching {endpoint} movies...")

        for page in range(1, 11):    

            print(f"Page {page}")

            url = (
                f"https://api.themoviedb.org/3/movie/"
                f"{endpoint}?api_key={api_key}&page={page}"
            )

            response = requests.get(url)
            data = response.json()

            for m in data["results"]:

                movie_id = m["id"]

                genres = []

                for gid in m["genre_ids"]:

                    if gid in genreids_map:
                        genres.append(genreids_map[gid])

                genres_string = ",".join(genres)

                year = None

                if m.get("release_date"):
                    try:
                        year = int(m["release_date"][:4])
                    except:
                        pass
                poster_url=backdrop_url=None
                if m.get("poster_path"):
                    poster_url="https://image.tmdb.org/t/p/w500"+ m["poster_path"]
                if m.get("backdrop_path"):
                    backdrop_url = ("https://image.tmdb.org/t/p/original"+ m["backdrop_path"])
                existing_movie = Movie.query.get(movie_id)
                if existing_movie:
                    existing_movie.poster_url=poster_url
                    existing_movie.backdrop_url=backdrop_url
                    updated+=1
                else:

                    movie = Movie(id=movie_id,title=m["title"],genres=genres_string,year=year,poster_url=poster_url,backdrop_url=backdrop_url)

                    db.session.add(movie)
                    added += 1

            db.session.commit()

    print("\nDone")
    print("Movies added:", added)
    print("Movies updated:", updated)
    print("Total movies in DB:", Movie.query.count())