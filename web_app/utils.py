import sys, logging, time
import requests, os
from requests.exceptions import RequestException, HTTPError, Timeout
from dotenv import load_dotenv
load_dotenv()

from web_app.models import Movie, API, Director, Genre, AgeRating, Series, Contingut

TMDB_API_KEY = os.getenv('THEMOVIEDB_API_KEY')

SERIES_ID_OFFSET = 100000
TMDB_MOVIE_URL = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query="
TMDB_SERIES_URL = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query="

TMDB_POSTER_URL = f"https://image.tmdb.org/t/p/w185/"  

DB_DATA = {
    
}

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


logger = logging.getLogger(__name__)

def get_poster(content_title, url_search, retries=3):
    """
    Busca el póster en TMDB con manejo de timeouts, rate limits y reintentos.
    """
    url = f"{url_search}{content_title}"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('results'):
                return None
                
            poster_path = data['results'][0].get('poster_path')
            
            if not poster_path:
                return None
                
            if poster_path.startswith('/'):
                poster_path = poster_path[1:]
                
            return f"{TMDB_POSTER_URL}{poster_path}"

        except HTTPError as e:
            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 2))
                logger.warning(f"TMDB Rate Limit alcanzado (429). Esperando {wait_time}s... (Intento {attempt + 1}/{retries})")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Error HTTP {response.status_code} buscando {content_title}: {e}")
                return None

        except Timeout:
            logger.warning(f"Timeout conectando con TMDB para {content_title}. (Intento {attempt + 1}/{retries})")
            time.sleep(1)
            continue
            
        except RequestException as e:
            logger.error(f"Fallo de red crítico con TMDB para {content_title}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error inesperado procesando póster de {content_title}: {e}")
            return None
            
    logger.error(f"Se agotaron los {retries} reintentos para descargar el póster de {content_title}.")
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
        
        directores_db = {d.director_id: d for d in Director.objects.filter(api=api_instance)}
        generos_db = {g.genre_id: g for g in Genre.objects.filter(api=api_instance)}
        age_ratings_db = {ar.age_rating_id: ar for ar in AgeRating.objects.filter(api=api_instance)}
        
        for json in unique_data:
            director = directores_db.get(json.get('director_id'))
            genre = generos_db.get(json.get('genre_id'))
            age_rating = age_ratings_db.get(json.get('age_rating_id'))

            contingut, created = Contingut.objects.get_or_create(
                titol=json['title'],
                data_estrena=json.get('year'),
                defaults={
                    'synopsis': json.get('synopsis'),
                    'rating': json.get('rating'),
                    'expires_at': json.get('expires_at'),
                    'director': director,
                    'genere': genre,
                    'age_rating': age_rating,
                    'poster_path': get_poster(json['title'], TMDB_MOVIE_URL),
                }
            )

            contingut.apis.add(api_instance)

            movie, movie_created = Movie.objects.get_or_create(contingut=contingut)
            
            status = "creada" if created else "vinculada a nueva plataforma"
            print(f"Movie '{movie.title}' {status} desde el puerto {port}.")
            
        current_ids = {json['id'] for json in unique_data}
        stale = Contingut.objects.filter(api=api_instance, movie__isnull=False).exclude(api_content_id__in=current_ids)
        if stale.exists():
            print(f"Cleaning {stale.count()} movies no longer in API {port}.")
            stale.update(api=None)


def get_series(params=None):
    series_data = Call('series', params=params)
    
    for port, data in series_data.items():
        if not data:
            continue
            
        api_instance = API.objects.get(port=port)
        unique_data = deduplicate_by_id(data)
        
        directores_db = {d.director_id: d for d in Director.objects.filter(api=api_instance)}
        generos_db = {g.genre_id: g for g in Genre.objects.filter(api=api_instance)}
        age_ratings_db = {ar.age_rating_id: ar for ar in AgeRating.objects.filter(api=api_instance)}
        
        for json in unique_data:
            director = directores_db.get(json.get('director_id'))
            genre = generos_db.get(json.get('genre_id'))
            age_rating = age_ratings_db.get(json.get('age_rating_id'))

            contingut, created = Contingut.objects.get_or_create(
                titol=json['title'],
                data_estrena=json.get('start_year'),
                defaults={
                    'synopsis': json.get('synopsis'),
                    'rating': json.get('rating'),
                    'expires_at': json.get('expires_at'),
                    'director': director,
                    'genere': genre,
                    'age_rating': age_rating,
                    'poster_path': get_poster(json['title'], TMDB_SERIES_URL),
                }
            )

            contingut.apis.add(api_instance)

            series, series_created = Series.objects.get_or_create(
                contingut=contingut,
                defaults={
                    'num_temporades': json.get('total_seasons'),
                }
            )
            
            status = "creada" if created else "vinculada a nueva plataforma"
            print(f"Series '{series.title}' {status} desde el puerto {port}.")

        current_ids = {json['id'] + SERIES_ID_OFFSET for json in unique_data}
        stale = Contingut.objects.filter(api=api_instance, series__isnull=False).exclude(api_content_id__in=current_ids)
        if stale.exists():
            print(f"Cleaning {stale.count()} series no longer in API {port}.")
            stale.update(api=None)

if __name__ == '__main__':
    store_data()
