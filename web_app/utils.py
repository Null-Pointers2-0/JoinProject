import sys
import requests, os

from dotenv import load_dotenv
load_dotenv()

from web_app.models import Movie, API, Director, Genre, AgeRating, Series, Contingut

TMDB_API_KEY = os.getenv('THEMOVIEDB_API_KEY')

SERIES_ID_OFFSET = 100000
TMDB_MOVIE_URL = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query="
TMDB_SERIES_URL = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query="

TMDB_POSTER_URL = f"https://image.tmdb.org/t/p/w185/"  

def store_data():
    for port in ['8080', '8081', '8082']:
        store_api(port)

    get_directors()
    get_genres()
    get_age_ratings()
    get_movies()
    get_series()


def store_api(port):
    API.objects.get_or_create(port=port)

def get_poster(content_title,url_search):
    try:
        response = requests.get(f"{url_search}{content_title}")
        response.raise_for_status()
        poster_path = response.json()['results'][0]['poster_path']
        if poster_path.startswith('/'):
            poster_path = poster_path[1:]
        return f"{TMDB_POSTER_URL}{poster_path}"
    except Exception as e:
        print(f"Error getting poster for '{content_title}': {e}")
        return None


def Call(endpoint, params=None):
    result = {'8080': None, '8081': None, '8082': None}
    APIs = [('8080', os.getenv('API_KEY_8080')), ('8081', os.getenv('API_KEY_8081')), ('8082', os.getenv('API_KEY_8082')), ('tmdb', os.getenv('THEMOVIEDB_API_KEY'))]

    print(f"Calling endpoint '{endpoint}' with params: {params}")
    for port, api_key in APIs:
        url = f'http://localhost:{port}/{endpoint}'
        headers = {'X-API-KEY': api_key}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=5)
            if r.status_code == 200:
                result[port] = r.json()
            print(f"Response from port {port}: {r.status_code} - {r.text[:100]}...")
        except requests.exceptions.ConnectionError:
            print(f"Failed to connect to {url}: Connection refused")
            result[port] = None
        except requests.exceptions.Timeout:
            print(f"Request to {url} timed out")
            result[port] = None
        except Exception as e:
            print(f"Error calling {url}: {e}")
            result[port] = None
    return result

def deduplicate_by_id(data):
    seen_ids = set()
    unique = []
    for item in data:
        item_id = item['id']
        if item_id not in seen_ids:
            seen_ids.add(item_id)
            unique.append(item)
    return unique

def get_directors():
    directors = Call('directors')
    for port, data in directors.items():
        if data is not None:
            for json in data:
                Director.objects.get_or_create(
                    director_id=json['id'],
                    api=API.objects.get(port=port),
                    defaults={
                        'name': json['name'],
                        'birth_date': json['birth_date'],
                        'country': json['country'],
                    }
                )

def get_genres():
    genres = Call('genres')
    for port, data in genres.items():
        if data is not None:
            for json in data:
                Genre.objects.get_or_create(
                    genre_id=json['id'],
                    api=API.objects.get(port=port),
                    defaults={
                        'name': json['name'],
                        'description': json['description'],
                    }
                )

def get_age_ratings():
    age_ratings = Call('age-ratings')
    for port, data in age_ratings.items():
        if data is not None:
            for json in data:
                AgeRating.objects.get_or_create(
                    age_rating_id=json['id'],
                    api=API.objects.get(port=port),
                    defaults={
                        'codi': json['description'],
                        'age': json['minimum_age'],
                    }
                )

def get_movies(params=None):
    movies_data = Call('movies', params=params)
    
    for port, data in movies_data.items():
        if not data:
            continue
            
        api_instance = API.objects.get(port=port)
        unique_data = deduplicate_by_id(data)
        
        for json in unique_data:
            director = Director.objects.filter(director_id=json.get('director_id')).first()
            genre = Genre.objects.filter(genre_id=json.get('genre_id')).first()
            age_rating = AgeRating.objects.filter(age_rating_id=json.get('age_rating_id'), api=api_instance).first()

            contingut, _ = Contingut.objects.update_or_create(
                api_content_id=json['id'],
                api=api_instance,
                defaults={
                    'titol': json['title'],
                    'data_estrena': json.get('year'),
                    'synopsis': json.get('synopsis'),
                    'rating': json.get('rating'),
                    'expires_at': json.get('expires_at'),
                    'director': director,
                    'genere': genre,
                    'age_rating': age_rating,
                    'poster_path': get_poster(json['title'], TMDB_MOVIE_URL),
                }
            )

            movie, created = Movie.objects.get_or_create(
                contingut=contingut,
            )
            
            status = "created" if created else "found"
            print(f"Movie '{movie.title}' {status} from port {port}.")


def get_series(params=None):
    series_data = Call('series', params=params)
    for port, data in series_data.items():
        if not data:
            continue
            
        api_instance = API.objects.get(port=port)
        unique_data = deduplicate_by_id(data)
        
        for json in unique_data:
            director = Director.objects.filter(director_id=json.get('director_id')).first()
            genre = Genre.objects.filter(genre_id=json.get('genre_id')).first()
            age_rating = AgeRating.objects.filter(age_rating_id=json.get('age_rating_id'), api=api_instance).first()

            contingut, _ = Contingut.objects.update_or_create(
                api_content_id=json['id'] + SERIES_ID_OFFSET,
                api=api_instance,
                defaults={
                    'titol': json['title'],
                    'data_estrena': json.get('start_year'),
                    'synopsis': json.get('synopsis'),
                    'rating': json.get('rating'),
                    'expires_at': json.get('expires_at'),
                    'director': director,
                    'genere': genre,
                    'age_rating': age_rating,
                    'poster_path': get_poster(json['title'], TMDB_SERIES_URL),
                }
            )

            series, created = Series.objects.get_or_create(
                contingut=contingut,
                defaults={
                    'num_temporades': json.get('total_seasons'),
                }
            )
            
            status = "created" if created else "found"
            print(f"Series '{series.title}' {status} from port {port}.")

if __name__ == '__main__':
    store_data()
