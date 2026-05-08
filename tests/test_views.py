from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from web_app.models import API, Director, Genre, AgeRating, Movie, Series, UserProfile
import io
from PIL import Image


CustomUser = get_user_model()


def create_test_image():
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer


class HomeViewTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8000, name='Netflix')
        self.genre = Genre.objects.create(genre_id=1, api=self.api, name='Action')
        self.director = Director.objects.create(
            director_id=1, api=self.api, name='Director',
            birth_date=timezone.now(), country='US'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=1, api=self.api, description='PG', age=10
        )
        self.movie = Movie.objects.create(
            movie_id=1, api=self.api, title='Movie One',
            genre=self.genre, director=self.director, age_rating=self.age_rating, year=2020
        )
        self.series = Series.objects.create(
            series_id=1, api=self.api, title='Series One',
            genre=self.genre, director=self.director, age_rating=self.age_rating,
            start_year=2020, total_seasons=3
        )

    def test_home_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home/home.html')

    def test_home_shows_movies_and_series(self):
        response = self.client.get(reverse('home'))
        self.assertIn('items', response.context)
        self.assertIn('genres', response.context)
        self.assertIn('directors', response.context)

    def test_home_search_filter(self):
        response = self.client.get(reverse('home'), {'q': 'Movie One'})
        titles = [item.title for item in response.context['items']]
        self.assertIn('Movie One', titles)
        self.assertNotIn('Series One', titles)

    def test_home_genre_filter(self):
        response = self.client.get(reverse('home'), {'genre': 'Action'})
        self.assertEqual(len(response.context['items']), 2)

    def test_home_director_filter(self):
        response = self.client.get(reverse('home'), {'director': 'Director'})
        self.assertEqual(len(response.context['items']), 2)

    def test_home_age_rating_filter(self):
        response = self.client.get(reverse('home'), {'age_rating': 'PG'})
        self.assertEqual(len(response.context['items']), 2)


class RegisterViewTest(TestCase):
    def test_register_get_status_code(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_uses_correct_template(self):
        response = self.client.get(reverse('register'))
        self.assertTemplateUsed(response, 'identify/register.html')

    def test_register_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@mail.com',
            'password': 'password123',
            'password2': 'password123',
            'terms_accepted': True,
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())

    def test_register_invalid_passwords(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@mail.com',
            'password': 'password123',
            'password2': 'different',
            'terms_accepted': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username='newuser').exists())


class UserSettingViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='password123')

    def test_user_setting_redirects_if_not_authenticated(self):
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
            age_rating_id=2, api=self.api, description='PG-13', age=13
        )
        self.movie = Movie.objects.create(
            movie_id=2, api=self.api, title='Test Movie',
            director=self.director, age_rating=self.age_rating, year=2021
        )
        self.user = CustomUser.objects.create_user(username='movieuser', password='password123')

    def test_movie_detail_status_code(self):
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)

    def test_movie_detail_template(self):
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertTemplateUsed(response, 'Details/details_movie.html')

    def test_movie_detail_404(self):
        response = self.client.get(reverse('movie_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_movie_detail_not_favorite_for_anonymous(self):
        response = self.client.get(reverse('movie_detail', args=[self.movie.id]))
        self.assertFalse(response.context['is_favorite'])

    def test_movie_detail_favorite_for_authenticated(self):
        self.client.login(username='movieuser', password='password123')
        profile = self.user.profile
        profile.favorite_movies.add(self.movie)
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
            age_rating_id=3, api=self.api, description='TV-MA', age=17
        )
        self.series = Series.objects.create(
            series_id=2, api=self.api, title='Test Series',
            director=self.director, age_rating=self.age_rating,
            start_year=2019, total_seasons=4
        )
        self.user = CustomUser.objects.create_user(username='seriesuser', password='password123')

    def test_series_detail_status_code(self):
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertEqual(response.status_code, 200)

    def test_series_detail_template(self):
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertTemplateUsed(response, 'Details/details_serie.html')

    def test_series_detail_404(self):
        response = self.client.get(reverse('series_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_series_detail_not_favorite_for_anonymous(self):
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertFalse(response.context['is_favorite'])

    def test_series_detail_favorite_for_authenticated(self):
        self.client.login(username='seriesuser', password='password123')
        profile = self.user.profile
        profile.favorite_series.add(self.series)
        response = self.client.get(reverse('series_detail', args=[self.series.id]))
        self.assertTrue(response.context['is_favorite'])


class ApiUserProfileTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='apiuser', password='password123',
            email='api@mail.com', first_name='John', last_name='Doe'
        )

    def test_api_profile_redirects_if_not_authenticated(self):
        response = self.client.get(reverse('api_user_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class ToggleMovieFavoriteTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8003, name='Disney')
        self.director = Director.objects.create(
            director_id=4, api=self.api, name='Dir3',
            birth_date=timezone.now(), country='ES'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=4, api=self.api, description='G', age=0
        )
        self.movie = Movie.objects.create(
            movie_id=3, api=self.api, title='Fav Movie',
            director=self.director, age_rating=self.age_rating, year=2022
        )
        self.user = CustomUser.objects.create_user(username='favuser', password='password123')

    def test_toggle_redirects_if_not_authenticated(self):
        response = self.client.post(reverse('toggle_movie_favorite', args=[self.movie.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_toggle_add_favorite(self):
        self.client.login(username='favuser', password='password123')
        response = self.client.post(reverse('toggle_movie_favorite', args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'added')
        self.assertIn(self.movie, self.user.profile.favorite_movies.all())

    def test_toggle_remove_favorite(self):
        self.client.login(username='favuser', password='password123')
        self.user.profile.favorite_movies.add(self.movie)
        response = self.client.post(reverse('toggle_movie_favorite', args=[self.movie.id]))
        data = response.json()
        self.assertEqual(data['status'], 'removed')
        self.assertNotIn(self.movie, self.user.profile.favorite_movies.all())

    def test_toggle_get_method_not_allowed(self):
        self.client.login(username='favuser', password='password123')
        response = self.client.get(reverse('toggle_movie_favorite', args=[self.movie.id]))
        self.assertEqual(response.status_code, 405)

    def test_toggle_404_for_nonexistent(self):
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
            age_rating_id=5, api=self.api, description='PG', age=7
        )
        self.series = Series.objects.create(
            series_id=3, api=self.api, title='Fav Series',
            director=self.director, age_rating=self.age_rating,
            start_year=2021, total_seasons=2
        )
        self.user = CustomUser.objects.create_user(username='favseriesuser', password='password123')

    def test_toggle_series_redirects_if_not_authenticated(self):
        response = self.client.post(reverse('toggle_series_favorite', args=[self.series.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_toggle_series_add_favorite(self):
        self.client.login(username='favseriesuser', password='password123')
        response = self.client.post(reverse('toggle_series_favorite', args=[self.series.id]))
        data = response.json()
        self.assertEqual(data['status'], 'added')
        self.assertIn(self.series, self.user.profile.favorite_series.all())

    def test_toggle_series_remove_favorite(self):
        self.client.login(username='favseriesuser', password='password123')
        self.user.profile.favorite_series.add(self.series)
        response = self.client.post(reverse('toggle_series_favorite', args=[self.series.id]))
        data = response.json()
        self.assertEqual(data['status'], 'removed')
        self.assertNotIn(self.series, self.user.profile.favorite_series.all())

    def test_toggle_series_get_method_not_allowed(self):
        self.client.login(username='favseriesuser', password='password123')
        response = self.client.get(reverse('toggle_series_favorite', args=[self.series.id]))
        self.assertEqual(response.status_code, 405)


class TermsAndPrivacyViewsTest(TestCase):
    def test_terms_use_status_code(self):
        response = self.client.get(reverse('terms_use'))
        self.assertEqual(response.status_code, 200)

    def test_terms_use_template(self):
        response = self.client.get(reverse('terms_use'))
        self.assertTemplateUsed(response, 'footer_legal/terms_use.html')

    def test_privacy_policy_status_code(self):
        response = self.client.get(reverse('privacy_policy'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy_template(self):
        response = self.client.get(reverse('privacy_policy'))
        self.assertTemplateUsed(response, 'footer_legal/privacy_policy.html')


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='profileuser', password='password123', email='prof@mail.com')

    def test_profile_redirects_if_not_authenticated(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_get_status_code(self):
        self.client.login(username='profileuser', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_post_updates_user(self):
        self.client.login(username='profileuser', password='password123')
        response = self.client.post(reverse('profile'), {
            'username': 'profileuser',
            'first_name': 'Updated',
            'last_name': 'Name',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_profile_post_with_avatar(self):
        self.client.login(username='profileuser', password='password123')
        img_buffer = create_test_image()
        from django.core.files.uploadedfile import SimpleUploadedFile
        img = SimpleUploadedFile('avatar.jpg', img_buffer.read(), content_type='image/jpeg')
        response = self.client.post(reverse('profile'), {
            'username': 'profileuser',
            'first_name': 'WithAvatar',
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
            age_rating_id=6, api=self.api, description='R', age=18
        )
        Movie.objects.create(
            movie_id=4, api=self.api, title='History Movie',
            director=self.director, age_rating=self.age_rating, year=2019
        )

    def test_history_redirects_if_not_authenticated(self):
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_history_get_status_code(self):
        self.client.login(username='histuser', password='password123')
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)

    def test_history_shows_movies(self):
        self.client.login(username='histuser', password='password123')
        response = self.client.get(reverse('history'))
        self.assertIn('movies', response.context)


class UserFollowedViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='followuser', password='password123')
        self.api = API.objects.create(port=8006, name='Follow')
        self.director = Director.objects.create(
            director_id=7, api=self.api, name='Dir6',
            birth_date=timezone.now(), country='DE'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=7, api=self.api, description='PG', age=10
        )
        self.movie = Movie.objects.create(
            movie_id=5, api=self.api, title='Follow Movie',
            director=self.director, age_rating=self.age_rating, year=2020
        )
        self.series = Series.objects.create(
            series_id=4, api=self.api, title='Follow Series',
            director=self.director, age_rating=self.age_rating,
            start_year=2020, total_seasons=1
        )

    def test_followed_redirects_if_not_authenticated(self):
        response = self.client.get(reverse('followed'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_followed_get_status_code(self):
        self.client.login(username='followuser', password='password123')
        response = self.client.get(reverse('followed'))
        self.assertEqual(response.status_code, 200)

    def test_followed_shows_favorites(self):
        self.client.login(username='followuser', password='password123')
        self.user.profile.favorite_movies.add(self.movie)
        self.user.profile.favorite_series.add(self.series)
        response = self.client.get(reverse('followed'))
        self.assertIn(self.movie, response.context['movies'])
        self.assertIn(self.series, response.context['series_list'])


class UserSubscriptionViewTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='subuser', password='password123')
        self.api1 = API.objects.create(port=8007, name='Sub1')
        self.api2 = API.objects.create(port=8008, name='Sub2')

    def test_subscription_redirects_if_not_authenticated(self):
        response = self.client.get(reverse('suscription'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_subscription_get_status_code(self):
        self.client.login(username='subuser', password='password123')
        response = self.client.get(reverse('suscription'))
        self.assertEqual(response.status_code, 200)

    def test_subscription_get_shows_apis(self):
        self.client.login(username='subuser', password='password123')
        response = self.client.get(reverse('suscription'))
        self.assertIn('all_apis', response.context)
        self.assertEqual(response.context['all_apis'].count(), 2)

    def test_subscription_post_updates_subscriptions(self):
        self.client.login(username='subuser', password='password123')
        response = self.client.post(reverse('suscription'), {
            'subscriptions': [self.api1.id],
        })
        self.assertRedirects(response, reverse('suscription'))
        self.user.refresh_from_db()
        self.assertIn(self.api1, self.user.subscriptions.all())
        self.assertNotIn(self.api2, self.user.subscriptions.all())

    def test_subscription_post_clears_subscriptions(self):
        self.client.login(username='subuser', password='password123')
        self.user.subscriptions.add(self.api1, self.api2)
        response = self.client.post(reverse('suscription'), {
            'subscriptions': [],
        })
        self.assertRedirects(response, reverse('suscription'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.subscriptions.count(), 0)
