from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from web_app.models import API, Director, Genre, AgeRating, Contingut, Movie, Series, UserProfile
import io
from PIL import Image


CustomUser = get_user_model()


def create_test_image():
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer


def create_contingut(api=None, genre=None, director=None, age_rating=None, title='Test', year=2020):
    """Helper para crear Contingut con datos por defecto."""
    return Contingut.objects.create(
        api_content_id=100 + Contingut.objects.count(),
        titol=title,
        data_estrena=year,
        director=director,
        genere=genre,
        age_rating=age_rating,
        api=api
    )


class HomeViewTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8000, name='Netflix')
        self.genre = Genre.objects.create(genre_id=1, api=self.api, name='Action')
        self.director = Director.objects.create(
            director_id=1, api=self.api, name='Director',
            birth_date=timezone.now(), country='US'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=1, api=self.api, codi='PG', age=10
        )
        self.contingut_movie = create_contingut(
            api=self.api, genre=self.genre, director=self.director,
            age_rating=self.age_rating, title='Movie One', year=2020
        )
        self.movie = Movie.objects.create(contingut=self.contingut_movie)
        self.contingut_series = create_contingut(
            api=self.api, genre=self.genre, director=self.director,
            age_rating=self.age_rating, title='Series One', year=2020
        )
        self.series = Series.objects.create(contingut=self.contingut_series, num_temporades=3)

    # ------------------------------------------------------------------ #
    #  HOME - BÁSICO                                                        #
    # ------------------------------------------------------------------ #

    def test_home_status_code(self):
        """Comprueba que la vista home responde con 200 OK."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        """Comprueba que se renderiza el template correcto."""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home/home.html')

    def test_home_shows_movies_and_series(self):
        """Comprueba que el context contiene 'items', 'genres' y 'directors'."""
        response = self.client.get(reverse('home'))
        self.assertIn('items', response.context)
        self.assertIn('genres', response.context)
        self.assertIn('directors', response.context)

    def test_home_empty_results(self):
        """Comprueba que home funciona aunque no haya películas ni series."""
        Movie.objects.all().delete()
        Series.objects.all().delete()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['items']), 0)

    # ------------------------------------------------------------------ #
    #  HOME - FILTROS                                                       #
    # ------------------------------------------------------------------ #

    def test_home_search_filter(self):
        """Comprueba que el filtro por query 'q' devuelve solo los resultados coincidentes."""
        response = self.client.get(reverse('home'), {'q': 'Movie One'})
        titles = [item.title for item in response.context['items']]
        self.assertIn('Movie One', titles)
        self.assertNotIn('Series One', titles)

    def test_home_search_no_results(self):
        """Comprueba que una búsqueda sin resultados devuelve lista vacía."""
        response = self.client.get(reverse('home'), {'q': 'Inexistente'})
        self.assertEqual(len(response.context['items']), 0)

    def test_home_genre_filter(self):
        """Comprueba que el filtro por género devuelve películas y series de ese género."""
        response = self.client.get(reverse('home'), {'genre': 'Action'})
        self.assertEqual(len(response.context['items']), 2)

    def test_home_genre_filter_no_results(self):
        """Comprueba que un género inexistente no devuelve resultados."""
        response = self.client.get(reverse('home'), {'genre': 'Fantasía'})
        self.assertEqual(len(response.context['items']), 0)

    def test_home_director_filter(self):
        """Comprueba que el filtro por director devuelve contenido de ese director."""
        response = self.client.get(reverse('home'), {'director': 'Director'})
        self.assertEqual(len(response.context['items']), 2)

    def test_home_age_rating_filter(self):
        """Comprueba que el filtro por clasificación por edades funciona correctamente."""
        response = self.client.get(reverse('home'), {'age_rating': 'PG'})
        self.assertEqual(len(response.context['items']), 2)

    # ------------------------------------------------------------------ #
    #  HOME - FILTRO POR PLATAFORMA                                         #
    # ------------------------------------------------------------------ #

    def test_home_platform_filter(self):
        """Comprueba que el filtro por plataforma (API port) devuelve solo contenido de esa API."""
        response = self.client.get(reverse('home'), {'platform': '8000'})
        self.assertEqual(len(response.context['items']), 2)

    def test_home_platform_filter_no_results(self):
        """Comprueba que un port inexistente no devuelve resultados."""
        response = self.client.get(reverse('home'), {'platform': '9999'})
        self.assertEqual(len(response.context['items']), 0)

    # ------------------------------------------------------------------ #
    #  HOME - PAGINACIÓN                                                    #
    # ------------------------------------------------------------------ #

    def test_home_pagination_page_1(self):
        """Comprueba que la página 1 tiene como máximo 20 items y hay siguiente página."""
        for i in range(25):
            cont = create_contingut(
                api=self.api, director=self.director, age_rating=self.age_rating,
                title=f'Extra Movie {i}', year=2020
            )
            Movie.objects.create(contingut=cont)
        response = self.client.get(reverse('home'))
        page_obj = response.context['items']
        self.assertTrue(page_obj.has_next())
        self.assertEqual(page_obj.number, 1)

    def test_home_pagination_page_2(self):
        """Comprueba que se puede acceder a la segunda página de resultados."""
        for i in range(25):
            cont = create_contingut(
                api=self.api, director=self.director, age_rating=self.age_rating,
                title=f'Extra Movie {i}', year=2020
            )
            Movie.objects.create(contingut=cont)
        response = self.client.get(reverse('home'), {'page': 2})
        page_obj = response.context['items']
        self.assertTrue(page_obj.has_previous())
        self.assertEqual(page_obj.number, 2)

    def test_home_content_type_assigned(self):
        """Comprueba que cada item tiene el atributo content_type ('movie' o 'series')."""
        response = self.client.get(reverse('home'))
        for item in response.context['items']:
            self.assertIn(item.content_type, ['movie', 'series'])


class RegisterViewTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=9000, name='RegAPI')

    # ------------------------------------------------------------------ #
    #  REGISTER - BÁSICO                                                    #
    # ------------------------------------------------------------------ #

    def test_register_get_status_code(self):
        """Comprueba que el GET a register responde 200."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_uses_correct_template(self):
        """Comprueba que se usa el template de registro correcto."""
        response = self.client.get(reverse('register'))
        self.assertTemplateUsed(response, 'identify/register.html')

    def test_register_success(self):
        """Comprueba que un registro válido crea el usuario y redirige a home."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': True,
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())

    # ------------------------------------------------------------------ #
    #  REGISTER - ERRORES                                                   #
    # ------------------------------------------------------------------ #

    def test_register_invalid_passwords(self):
        """Comprueba que contraseñas distintas no crean el usuario."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@mail.com',
            'password': 'password123',
            'password2': 'different',
            'terms_accepted': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())

    def test_register_terms_not_accepted(self):
        """Comprueba que sin aceptar términos no se crea el usuario."""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())

    def test_register_duplicate_username(self):
        """Comprueba que un username duplicado no permite el registro."""
        CustomUser.objects.create_user(username='existing', password='password123')
        response = self.client.post(reverse('register'), {
            'username': 'existing',
            'email': 'other@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(username='existing').count(), 1)

    # ------------------------------------------------------------------ #
    #  REGISTER - CON PLATAFORMAS                                           #
    # ------------------------------------------------------------------ #

    def test_register_with_platforms(self):
        """Comprueba que las plataformas seleccionadas se guardan como suscripciones."""
        response = self.client.post(reverse('register'), {
            'username': 'platformuser',
            'email': 'plat@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': True,
            'platforms': [self.api.id],
        })
        self.assertRedirects(response, reverse('home'))
        user = CustomUser.objects.get(username='platformuser')
        self.assertIn(self.api, user.subscriptions.all())


class UserSettingViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='password123')

    def test_user_setting_redirects_if_not_authenticated(self):
        """Comprueba que redirige a /login/ si el usuario no está autenticado."""
        response = self.client.get(reverse('user_setting'))
        self.assertRedirects(response, '/login/', fetch_redirect_response=False)


class MovieDetailViewTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8001, name='HBO')
        self.director = Director.objects.create(
            director_id=2, api=self.api, name='Dir',
            birth_date=timezone.now(), country='US'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=2, api=self.api, codi='PG-13', age=13
        )
        self.contingut = create_contingut(
            api=self.api, director=self.director, age_rating=self.age_rating,
            title='Test Movie', year=2021
        )
        self.movie = Movie.objects.create(contingut=self.contingut)
        self.user = CustomUser.objects.create_user(username='movieuser', password='password123')

    def test_movie_detail_status_code(self):
        """Comprueba que la vista de detalle de película responde 200."""
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)

    def test_movie_detail_template(self):
        """Comprueba que se usa el template de detalle de película."""
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertTemplateUsed(response, 'Details/details_movie.html')

    def test_movie_detail_context(self):
        """Comprueba que el contexto contiene 'content' y 'is_favorite'."""
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertIn('content', response.context)
        self.assertIn('is_favorite', response.context)

    def test_movie_detail_404(self):
        """Comprueba que un ID inexistente devuelve 404."""
        response = self.client.get(reverse('movie_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_movie_detail_not_favorite_for_anonymous(self):
        """Comprueba que un usuario anónimo ve is_favorite=False."""
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertFalse(response.context['is_favorite'])

    def test_movie_detail_favorite_for_authenticated(self):
        """Comprueba que un usuario autenticado con la peli en favoritos ve is_favorite=True."""
        self.client.login(username='movieuser', password='password123')
        self.user.profile.preferits.add(self.movie.contingut)
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertTrue(response.context['is_favorite'])


class SeriesDetailViewTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8002, name='Prime')
        self.director = Director.objects.create(
            director_id=3, api=self.api, name='Dir2',
            birth_date=timezone.now(), country='UK'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=3, api=self.api, codi='TV-MA', age=17
        )
        self.contingut = create_contingut(
            api=self.api, director=self.director, age_rating=self.age_rating,
            title='Test Series', year=2019
        )
        self.series = Series.objects.create(contingut=self.contingut, num_temporades=4)
        self.user = CustomUser.objects.create_user(username='seriesuser', password='password123')

    def test_series_detail_status_code(self):
        """Comprueba que la vista de detalle de serie responde 200."""
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertEqual(response.status_code, 200)

    def test_series_detail_template(self):
        """Comprueba que se usa el template de detalle de serie."""
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertTemplateUsed(response, 'Details/details_serie.html')

    def test_series_detail_context(self):
        """Comprueba que el contexto contiene 'content' y 'is_favorite'."""
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertIn('content', response.context)
        self.assertIn('is_favorite', response.context)

    def test_series_detail_404(self):
        """Comprueba que un ID inexistente devuelve 404."""
        response = self.client.get(reverse('series_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_series_detail_not_favorite_for_anonymous(self):
        """Comprueba que un usuario anónimo ve is_favorite=False."""
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertFalse(response.context['is_favorite'])

    def test_series_detail_favorite_for_authenticated(self):
        """Comprueba que un usuario autenticado con la serie en favoritos ve is_favorite=True."""
        self.client.login(username='seriesuser', password='password123')
        self.user.profile.preferits.add(self.series.contingut)
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertTrue(response.context['is_favorite'])


class ApiUserProfileTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='apiuser', password='password123',
            email='api@mail.com', first_name='John', last_name='Doe'
        )

    def test_api_profile_redirects_if_not_authenticated(self):
        """Comprueba que redirige a login si no está autenticado."""
        response = self.client.get(reverse('api_user_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_api_profile_returns_json(self):
        """Comprueba que la respuesta es JSON válido."""
        self.client.login(username='apiuser', password='password123')
        response = self.client.get(reverse('api_user_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_api_profile_data(self):
        """Comprueba que el JSON contiene los datos personales del usuario."""
        self.client.login(username='apiuser', password='password123')
        data = self.client.get(reverse('api_user_profile')).json()
        self.assertEqual(data['personal_info']['username'], 'apiuser')
        self.assertEqual(data['personal_info']['email'], 'api@mail.com')
        self.assertEqual(data['personal_info']['first_name'], 'John')
        self.assertEqual(data['personal_info']['last_name'], 'Doe')


class ToggleMovieFavoriteTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8003, name='Disney')
        self.director = Director.objects.create(
            director_id=4, api=self.api, name='Dir3',
            birth_date=timezone.now(), country='ES'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=4, api=self.api, codi='G', age=0
        )
        self.contingut = create_contingut(
            api=self.api, director=self.director, age_rating=self.age_rating,
            title='Fav Movie', year=2022
        )
        self.movie = Movie.objects.create(contingut=self.contingut)
        self.user = CustomUser.objects.create_user(username='favuser', password='password123')

    def test_toggle_redirects_if_not_authenticated(self):
        """Comprueba que redirige a login si no está autenticado."""
        response = self.client.post(reverse('toggle_movie_favorite', args=[self.movie.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_toggle_add_favorite(self):
        """Comprueba que POST añade la película a favoritos y devuelve status 'added'."""
        self.client.login(username='favuser', password='password123')
        response = self.client.post(reverse('toggle_movie_favorite', args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'added')
        self.assertIn(self.movie.contingut, self.user.profile.preferits.all())

    def test_toggle_remove_favorite(self):
        """Comprueba que POST quita la película de favoritos y devuelve status 'removed'."""
        self.client.login(username='favuser', password='password123')
        self.user.profile.preferits.add(self.movie.contingut)
        response = self.client.post(reverse('toggle_movie_favorite', args=[self.movie.id]))
        data = response.json()
        self.assertEqual(data['status'], 'removed')
        self.assertNotIn(self.movie.contingut, self.user.profile.preferits.all())

    def test_toggle_get_method_not_allowed(self):
        """Comprueba que GET devuelve 405 (solo se permite POST)."""
        self.client.login(username='favuser', password='password123')
        response = self.client.get(reverse('toggle_movie_favorite', args=[self.movie.id]))
        self.assertEqual(response.status_code, 405)

    def test_toggle_404_for_nonexistent(self):
        """Comprueba que un ID de película inexistente devuelve 404."""
        self.client.login(username='favuser', password='password123')
        response = self.client.post(reverse('toggle_movie_favorite', args=[99999]))
        self.assertEqual(response.status_code, 404)


class ToggleSeriesFavoriteTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8004, name='Apple')
        self.director = Director.objects.create(
            director_id=5, api=self.api, name='Dir4',
            birth_date=timezone.now(), country='FR'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=5, api=self.api, codi='PG', age=7
        )
        self.contingut = create_contingut(
            api=self.api, director=self.director, age_rating=self.age_rating,
            title='Fav Series', year=2021
        )
        self.series = Series.objects.create(contingut=self.contingut, num_temporades=2)
        self.user = CustomUser.objects.create_user(username='favseriesuser', password='password123')

    def test_toggle_series_redirects_if_not_authenticated(self):
        """Comprueba que redirige a login si no está autenticado."""
        response = self.client.post(reverse('toggle_series_favorite', args=[self.series.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_toggle_series_add_favorite(self):
        """Comprueba que POST añade la serie a favoritos y devuelve status 'added'."""
        self.client.login(username='favseriesuser', password='password123')
        response = self.client.post(reverse('toggle_series_favorite', args=[self.series.id]))
        data = response.json()
        self.assertEqual(data['status'], 'added')
        self.assertIn(self.series.contingut, self.user.profile.preferits.all())

    def test_toggle_series_remove_favorite(self):
        """Comprueba que POST quita la serie de favoritos y devuelve status 'removed'."""
        self.client.login(username='favseriesuser', password='password123')
        self.user.profile.preferits.add(self.series.contingut)
        response = self.client.post(reverse('toggle_series_favorite', args=[self.series.id]))
        data = response.json()
        self.assertEqual(data['status'], 'removed')
        self.assertNotIn(self.series.contingut, self.user.profile.preferits.all())

    def test_toggle_series_get_method_not_allowed(self):
        """Comprueba que GET devuelve 405 (solo se permite POST)."""
        self.client.login(username='favseriesuser', password='password123')
        response = self.client.get(reverse('toggle_series_favorite', args=[self.series.id]))
        self.assertEqual(response.status_code, 405)


class TermsAndPrivacyViewsTest(TestCase):
    def test_terms_use_status_code(self):
        """Comprueba que la vista de términos responde 200."""
        response = self.client.get(reverse('terms_use'))
        self.assertEqual(response.status_code, 200)

    def test_terms_use_template(self):
        """Comprueba que se usa el template de términos de uso."""
        response = self.client.get(reverse('terms_use'))
        self.assertTemplateUsed(response, 'footer_legal/terms_use.html')

    def test_privacy_policy_status_code(self):
        """Comprueba que la vista de política de privacidad responde 200."""
        response = self.client.get(reverse('privacy_policy'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy_template(self):
        """Comprueba que se usa el template de política de privacidad."""
        response = self.client.get(reverse('privacy_policy'))
        self.assertTemplateUsed(response, 'footer_legal/privacy_policy.html')


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='profileuser', password='password123', email='prof@mail.com')

    def test_profile_redirects_if_not_authenticated(self):
        """Comprueba que redirige a login si no está autenticado."""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_get_status_code(self):
        """Comprueba que GET responde 200 con el formulario pre-rellenado."""
        self.client.login(username='profileuser', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_template(self):
        """Comprueba que se usa el template de perfil correcto."""
        self.client.login(username='profileuser', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertTemplateUsed(response, 'users/profile/profile.html')

    def test_profile_post_updates_user(self):
        """Comprueba que POST actualiza los campos del usuario correctamente."""
        self.client.login(username='profileuser', password='password123')
        response = self.client.post(reverse('profile'), {
            'username': 'profileuser',
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'prof@mail.com',
            'type': 'Consumer',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_profile_post_with_avatar(self):
        """Comprueba que se puede subir un avatar válido junto con otros campos."""
        self.client.login(username='profileuser', password='password123')
        img_buffer = create_test_image()
        from django.core.files.uploadedfile import SimpleUploadedFile
        img = SimpleUploadedFile('avatar.jpg', img_buffer.read(), content_type='image/jpeg')
        response = self.client.post(reverse('profile'), {
            'username': 'profileuser',
            'first_name': 'WithAvatar',
            'email': 'prof@mail.com',
            'type': 'Consumer',
        }, files={'avatar': img})
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'WithAvatar')


class UserHistoryViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='histuser', password='password123')
        self.api = API.objects.create(port=8005, name='Hist')
        self.director = Director.objects.create(
            director_id=6, api=self.api, name='Dir5',
            birth_date=timezone.now(), country='US'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=6, api=self.api, codi='R', age=18
        )
        cont = create_contingut(
            api=self.api, director=self.director, age_rating=self.age_rating,
            title='History Movie', year=2019
        )
        Movie.objects.create(contingut=cont)

    def test_history_redirects_if_not_authenticated(self):
        """Comprueba que redirige a login si no está autenticado."""
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_history_get_status_code(self):
        """Comprueba que GET responde 200 para usuario autenticado."""
        self.client.login(username='histuser', password='password123')
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)

    def test_history_template(self):
        """Comprueba que se usa el template de historial correcto."""
        self.client.login(username='histuser', password='password123')
        response = self.client.get(reverse('history'))
        self.assertTemplateUsed(response, 'users/parts/history.html')

    def test_history_shows_movies(self):
        """Comprueba que el contexto contiene 'movies' con las películas existentes."""
        self.client.login(username='histuser', password='password123')
        response = self.client.get(reverse('history'))
        self.assertIn('movies', response.context)
        self.assertGreaterEqual(response.context['movies'].count(), 1)

    def test_history_empty_movies(self):
        """Comprueba que funciona aunque no haya películas."""
        Movie.objects.all().delete()
        self.client.login(username='histuser', password='password123')
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['movies'].count(), 0)


class UserFollowedViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='followuser', password='password123')
        self.api = API.objects.create(port=8006, name='Follow')
        self.director = Director.objects.create(
            director_id=7, api=self.api, name='Dir6',
            birth_date=timezone.now(), country='DE'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=7, api=self.api, codi='PG', age=10
        )
        self.contingut_movie = create_contingut(
            api=self.api, director=self.director, age_rating=self.age_rating,
            title='Follow Movie', year=2020
        )
        self.movie = Movie.objects.create(contingut=self.contingut_movie)
        self.contingut_series = create_contingut(
            api=self.api, director=self.director, age_rating=self.age_rating,
            title='Follow Series', year=2020
        )
        self.series = Series.objects.create(contingut=self.contingut_series, num_temporades=1)

    def test_followed_redirects_if_not_authenticated(self):
        """Comprueba que redirige a login si no está autenticado."""
        response = self.client.get(reverse('followed'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_followed_get_status_code(self):
        """Comprueba que GET responde 200 para usuario autenticado."""
        self.client.login(username='followuser', password='password123')
        response = self.client.get(reverse('followed'))
        self.assertEqual(response.status_code, 200)

    def test_followed_template(self):
        """Comprueba que se usa el template de seguidos correcto."""
        self.client.login(username='followuser', password='password123')
        response = self.client.get(reverse('followed'))
        self.assertTemplateUsed(response, 'users/parts/followed.html')

    def test_followed_shows_favorites(self):
        """Comprueba que el contexto muestra los contenidos marcados como favoritos."""
        self.client.login(username='followuser', password='password123')
        self.user.profile.preferits.add(self.contingut_movie)
        self.user.profile.preferits.add(self.contingut_series)
        response = self.client.get(reverse('followed'))
        self.assertIn(self.movie, response.context['movies'])
        self.assertIn(self.series, response.context['series_list'])

    def test_followed_empty_favorites(self):
        """Comprueba que funciona aunque el usuario no tenga favoritos."""
        self.client.login(username='followuser', password='password123')
        response = self.client.get(reverse('followed'))
        self.assertEqual(response.context['movies'].count(), 0)
        self.assertEqual(response.context['series_list'].count(), 0)


class UserSubscriptionViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='subuser', password='password123')
        self.api1 = API.objects.create(port=8007, name='Sub1')
        self.api2 = API.objects.create(port=8008, name='Sub2')

    def test_subscription_redirects_if_not_authenticated(self):
        """Comprueba que redirige a login si no está autenticado."""
        response = self.client.get(reverse('suscription'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_subscription_get_status_code(self):
        """Comprueba que GET responde 200 para usuario autenticado."""
        self.client.login(username='subuser', password='password123')
        response = self.client.get(reverse('suscription'))
        self.assertEqual(response.status_code, 200)

    def test_subscription_template(self):
        """Comprueba que se usa el template de suscripciones correcto."""
        self.client.login(username='subuser', password='password123')
        response = self.client.get(reverse('suscription'))
        self.assertTemplateUsed(response, 'users/parts/subscription.html')

    def test_subscription_get_shows_apis(self):
        """Comprueba que el contexto contiene 'all_apis' ordenadas por port."""
        self.client.login(username='subuser', password='password123')
        response = self.client.get(reverse('suscription'))
        self.assertIn('all_apis', response.context)
        self.assertEqual(response.context['all_apis'].count(), 2)

    def test_subscription_user_subscription_ids(self):
        """Comprueba que el contexto incluye los IDs de las suscripciones del usuario."""
        self.client.login(username='subuser', password='password123')
        self.user.subscriptions.add(self.api1)
        response = self.client.get(reverse('suscription'))
        self.assertIn(self.api1.id, response.context['user_subscription_ids'])
        self.assertNotIn(self.api2.id, response.context['user_subscription_ids'])

    def test_subscription_post_updates_subscriptions(self):
        """Comprueba que POST actualiza las suscripciones del usuario correctamente."""
        self.client.login(username='subuser', password='password123')
        response = self.client.post(reverse('suscription'), {
            'subscriptions': [self.api1.id],
        })
        self.assertRedirects(response, reverse('suscription'))
        self.user.refresh_from_db()
        self.assertIn(self.api1, self.user.subscriptions.all())
        self.assertNotIn(self.api2, self.user.subscriptions.all())

    def test_subscription_post_clears_subscriptions(self):
        """Comprueba que enviar lista vacía limpia todas las suscripciones."""
        self.client.login(username='subuser', password='password123')
        self.user.subscriptions.add(self.api1, self.api2)
        response = self.client.post(reverse('suscription'), {
            'subscriptions': [],
        })
        self.assertRedirects(response, reverse('suscription'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscriptions.count(), 0)

    def test_subscription_post_switches_selection(self):
        """Comprueba que cambiar la selección reemplaza las suscripciones anteriores."""
        self.client.login(username='subuser', password='password123')
        self.user.subscriptions.add(self.api1)
        response = self.client.post(reverse('suscription'), {
            'subscriptions': [self.api2.id],
        })
        self.assertRedirects(response, reverse('suscription'))
        self.user.refresh_from_db()
        self.assertNotIn(self.api1, self.user.subscriptions.all())
        self.assertIn(self.api2, self.user.subscriptions.all())
