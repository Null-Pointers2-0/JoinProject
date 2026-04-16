import sys

import requests, os, django
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()
from web_app.models import Movie, API, Director, Genre, AgeRating, Series
load_dotenv()

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

def Call(endpoint, params=None):
    result = {'8080': None, '8081': None, '8082': None}
    APIs = [('8080', os.getenv('API_KEY_8080')), ('8081', os.getenv('API_KEY_8081')), ('8082', os.getenv('API_KEY_8082'))]

    print(f"Calling endpoint '{endpoint}' with params: {params}")
    for port, api_key in APIs:
        url = f'http://localhost:{port}/{endpoint}'
        headers = {'X-API-KEY': api_key}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            result[port] = r.json()
        print(f"Response from port {port}: {r.status_code} - {r.text[:100]}...")  # Log status and a snippet of the response
    return result

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
                        'description': json['description'],
                        'age': json['minimum_age'],
                    }
                )

def get_movies(params=None):
    movies_data = Call('movies', params=params)
    
    for port, data in movies_data.items():
        if not data:
            continue
            
        api_instance = API.objects.get(port=port)
        
        for json in data:
            movie, created = Movie.objects.update_or_create(
                movie_id=json['id'],
                api=api_instance,
                defaults={
                    'title': json['title'],
                    'synopsis': json.get('synopsis'),
                    'year': json.get('year'),
                    'rating': json.get('rating'),
                    'expires_at': json.get('expires_at'),
                    'director': Director.objects.filter(director_id=json.get('director_id')).first(),
                    'genre': Genre.objects.filter(genre_id=json.get('genre_id')).first(),
                    'age_rating': AgeRating.objects.filter(age_rating_id=json.get('age_rating_id'), api=api_instance).first(),
                }
            )
            
            status = "created" if created else "updated"
            print(f"Movie '{movie.title}' {status} from port {port}.")


def get_series(params=None):
    series_data = Call('series', params=params)
    for port, data in series_data.items():
        if not data:
            continue
            
        api_instance = API.objects.get(port=port)
        
        for json in data:
            series, created = Series.objects.update_or_create(
                series_id=json['id'],
                api=api_instance,
                defaults={
                    'title': json['title'],
                    'synopsis': json.get('synopsis'),
                    'start_year': json.get('start_year'),
                    'end_year': json.get('end_year'),
                    'total_seasons': json.get('total_seasons'),
                    'rating': json.get('rating'),
                    'expires_at': json.get('expires_at'),
                    'director': Director.objects.filter(director_id=json.get('director_id')).first(),
                    'genre': Genre.objects.filter(genre_id=json.get('genre_id')).first(),
                    'age_rating': AgeRating.objects.filter(age_rating_id=json.get('age_rating_id'), api=api_instance).first(),
                    'country_id': json.get('country_id'),
                    'language_id': json.get('language_id'),
                }
            )
            
            status = "created" if created else "updated"
            print(f"Series '{series.title}' {status} from port {port}.")

if __name__ == '__main__':
    store_data()