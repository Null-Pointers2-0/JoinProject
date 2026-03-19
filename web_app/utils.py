import requests, os
from dotenv import load_dotenv
load_dotenv()

def Call(endpoint, params=None):
    result = {'8080': None, '8081': None, '8082': None}
    APIs = [('8080', os.getenv('API_KEY_1')), ('8081', os.getenv('API_KEY_2')), ('8082', os.getenv('API_KEY_3'))]
    for port, api_key in APIs:
        url = f'http://localhost:{port}/{endpoint}'
        headers = {'X-API-KEY': api_key}
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            result[port] = r.json()
    return result


def get_movies(params=None):
    return Call('movies', params=params)

def get_series(params=None):
    return Call('series', params=params)

def get_directors():
    return Call('directors')

def get_genres():
    return Call('genres')

def get_age_ratings():
    return Call('age_ratings')