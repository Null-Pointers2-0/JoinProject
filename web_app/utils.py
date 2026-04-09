import sys
import requests, os, django
from dotenv import load_dotenv
from django.utils import timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
django.setup()

from web_app.models import Movie, API, Director, Genre, AgeRating, SyncLog

load_dotenv()


def store_data():
    log = SyncLog.objects.create(status="Running", summary="Synchronizing catalog from APIs...")
    stats = {'created': 0, 'updated': 0}

    try:
        for port in ['8080', '8081', '8082']:
            store_api(port)

        get_directors(stats)
        get_genres(stats)
        get_age_ratings(stats)
        get_movies(stats)
        log.status = "Success"
        log.summary = "Synchronization completed successfully."

    except Exception as e:
        log.status = "Error"
        log.summary = f"Error during synchronization: {str(e)}"
        print(f"Error: {e}")

    log.records_created = stats['created']
    log.records_updated = stats['updated']
    log.end_time = timezone.now()
    log.save()
    print(f"Log saved: {stats['created']} created, {stats['updated']} updated.")

def store_api(port):
    API.objects.get_or_create(port=port)

def Call(endpoint, params=None):
    result = {'8080': None, '8081': None, '8082': None}
    APIs = [('8080', os.getenv('API_KEY_8080')), ('8081', os.getenv('API_KEY_8081')),
            ('8082', os.getenv('API_KEY_8082'))]

    for port, api_key in APIs:
        url = f'http://localhost:{port}/{endpoint}'
        headers = {'X-API-KEY': api_key}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            result[port] = r.json()
    return result

def get_directors(stats):
    directors = Call('directors')
    for port, data in directors.items():
        if data is not None:
            for json in data:
                obj, created = Director.objects.get_or_create(
                    director_id=json['id'],
                    api=API.objects.get(port=port),
                    defaults={
                        'name': json['name'],
                        'birth_date': json['birth_date'],
                        'country': json['country'],
                    }
                )
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1

def get_genres(stats):
    genres = Call('genres')
    for port, data in genres.items():
        if data is not None:
            for json in data:
                obj, created = Genre.objects.get_or_create(
                    genre_id=json['id'],
                    api=API.objects.get(port=port),
                    defaults={
                        'name': json['name'],
                        'description': json['description'],
                    }
                )
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1

def get_age_ratings(stats):
    age_ratings = Call('age-ratings')
    for port, data in age_ratings.items():
        if data is not None:
            for json in data:
                obj, created = AgeRating.objects.get_or_create(
                    age_rating_id=json['id'],
                    api=API.objects.get(port=port),
                    defaults={
                        'description': json['description'],
                        'age': json['minimum_age'],
                    }
                )
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1

def get_movies(stats, params=None):
    movies_data = Call('movies', params=params)
    for port, data in movies_data.items():
        if not data: continue
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
                    'age_rating': AgeRating.objects.filter(age_rating_id=json.get('age_rating_id'),
                                                           api=api_instance).first(),
                }
            )
            if created:
                stats['created'] += 1
            else:
                stats['updated'] += 1

def get_series(params=None):
    return Call('series', params=params)