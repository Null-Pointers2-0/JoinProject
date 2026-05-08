from django.test import TestCase
from django.utils import timezone
from web_app.models import API, Director, Genre, AgeRating, Movie, Series, CustomUser, UserProfile, SyncLog


class APITest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8000, name='Netflix')

    def test_api_creation(self):
        self.assertEqual(self.api.port, 8000)
        self.assertEqual(self.api.name, 'Netflix')

    def test_api_str_with_name(self):
        self.assertEqual(str(self.api), 'Netflix')

    def test_api_str_without_name(self):
        api_no_name = API.objects.create(port=9000)
        self.assertEqual(str(api_no_name), 'API on port 9000')

    def test_api_port_unique(self):
        with self.assertRaises(Exception):
            API.objects.create(port=8000, name='Duplicate')


class DirectorTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8000, name='Netflix')
        self.director = Director.objects.create(
            director_id=1,
            api=self.api,
            name='Christopher Nolan',
            birth_date=timezone.now(),
            country='UK'
        )

    def test_director_creation(self):
        self.assertEqual(self.director.name, 'Christopher Nolan')
        self.assertEqual(self.director.api, self.api)

    def test_director_str(self):
        self.assertEqual(str(self.director), 'Christopher Nolan')

    def test_director_unique_together(self):
        with self.assertRaises(Exception):
            Director.objects.create(
                director_id=1,
                api=self.api,
                name='Duplicate',
                birth_date=timezone.now(),
                country='US'
            )


class GenreTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8001, name='HBO')
        self.genre = Genre.objects.create(
            genre_id=1,
            api=self.api,
            name='Sci-Fi',
            description='Science fiction genre'
        )

    def test_genre_creation(self):
        self.assertEqual(self.genre.name, 'Sci-Fi')
        self.assertEqual(self.genre.description, 'Science fiction genre')

    def test_genre_str(self):
        self.assertEqual(str(self.genre), 'Sci-Fi')

    def test_genre_unique_together(self):
        with self.assertRaises(Exception):
            Genre.objects.create(
                genre_id=1,
                api=self.api,
                name='Duplicate',
                description='Test'
            )


class AgeRatingTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8002, name='Disney')
        self.age_rating = AgeRating.objects.create(
            age_rating_id=1,
            api=self.api,
            description='PG-13',
            age=13
        )

    def test_age_rating_creation(self):
        self.assertEqual(self.age_rating.description, 'PG-13')
        self.assertEqual(self.age_rating.age, 13)

    def test_age_rating_str(self):
        self.assertEqual(str(self.age_rating), 'PG-13')

    def test_age_rating_unique_together(self):
        with self.assertRaises(Exception):
            AgeRating.objects.create(
                age_rating_id=1,
                api=self.api,
                description='Duplicate',
                age=13
            )


class MovieTest(TestCase):
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
            movie_id=1,
            api=self.api,
            title='Inception',
            genre=self.genre,
            director=self.director,
            age_rating=self.age_rating,
            year=2010,
            rating=8.8
        )

    def test_movie_creation(self):
        self.assertEqual(self.movie.title, 'Inception')
        self.assertEqual(self.movie.year, 2010)
        self.assertEqual(self.movie.rating, 8.8)

    def test_movie_str(self):
        self.assertEqual(str(self.movie), 'Inception')

    def test_movie_unique_together(self):
        with self.assertRaises(Exception):
            Movie.objects.create(
                movie_id=1,
                api=self.api,
                title='Duplicate',
                genre=self.genre,
                director=self.director,
                age_rating=self.age_rating
            )

    def test_get_similar_by_genre(self):
        Movie.objects.create(
            movie_id=2, api=self.api, title='Action Movie 2',
            genre=self.genre, director=self.director, age_rating=self.age_rating
        )
        Movie.objects.create(
            movie_id=3, api=self.api, title='Action Movie 3',
            genre=self.genre, director=self.director, age_rating=self.age_rating
        )
        similar = self.movie.get_similar_by_genre()
        self.assertEqual(similar.count(), 2)

    def test_get_similar_by_genre_no_genre(self):
        movie_no_genre = Movie.objects.create(
            movie_id=4, api=self.api, title='No Genre',
            director=self.director, age_rating=self.age_rating
        )
        similar = movie_no_genre.get_similar_by_genre()
        self.assertEqual(similar.count(), 0)


class SeriesTest(TestCase):
    def setUp(self):
        self.api = API.objects.create(port=8000, name='Netflix')
        self.genre = Genre.objects.create(genre_id=2, api=self.api, name='Drama')
        self.director = Director.objects.create(
            director_id=2, api=self.api, name='Series Director',
            birth_date=timezone.now(), country='US'
        )
        self.age_rating = AgeRating.objects.create(
            age_rating_id=2, api=self.api, description='TV-MA', age=17
        )
        self.series = Series.objects.create(
            series_id=1,
            api=self.api,
            title='Breaking Bad',
            genre=self.genre,
            director=self.director,
            age_rating=self.age_rating,
            start_year=2008,
            end_year=2013,
            total_seasons=5,
            rating=9.5
        )

    def test_series_creation(self):
        self.assertEqual(self.series.title, 'Breaking Bad')
        self.assertEqual(self.series.start_year, 2008)
        self.assertEqual(self.series.end_year, 2013)
        self.assertEqual(self.series.total_seasons, 5)

    def test_series_str(self):
        self.assertEqual(str(self.series), 'Breaking Bad')

    def test_series_year_property(self):
        self.assertEqual(self.series.year, 2008)

    def test_series_unique_together(self):
        with self.assertRaises(Exception):
            Series.objects.create(
                series_id=1,
                api=self.api,
                title='Duplicate',
                genre=self.genre,
                director=self.director,
                age_rating=self.age_rating
            )


class CustomUserTest(TestCase):
    def test_user_creation(self):
        user = CustomUser.objects.create_user(username='testuser', password='password123', email='test@mail.com')
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@mail.com')
        self.assertTrue(user.check_password('password123'))

    def test_user_str(self):
        user = CustomUser.objects.create_user(username='testuser2', password='password123')
        self.assertEqual(str(user), 'testuser2')


class UserProfileTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='profileuser', password='password123')
        self.api = API.objects.create(port=8003, name='Prime')
        self.profile = self.user.profile

    def test_profile_creation(self):
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(str(self.profile), 'Perfil de profileuser')

    def test_profile_favorite_movies(self):
        director = Director.objects.create(
            director_id=3, api=self.api, name='Dir',
            birth_date=timezone.now(), country='US'
        )
        age_rating = AgeRating.objects.create(
            age_rating_id=3, api=self.api, description='G', age=0
        )
        movie = Movie.objects.create(
            movie_id=5, api=self.api, title='Fav Movie',
            director=director, age_rating=age_rating
        )
        self.profile.favorite_movies.add(movie)
        self.assertIn(movie, self.profile.favorite_movies.all())


class SyncLogTest(TestCase):
    def test_sync_log_creation(self):
        log = SyncLog.objects.create(
            status='completed',
            summary='Test sync',
            records_created=10,
            records_updated=5
        )
        self.assertEqual(log.status, 'completed')
        self.assertEqual(log.records_created, 10)
        self.assertEqual(log.records_updated, 5)
        self.assertIsNotNone(log.start_time)

    def test_sync_log_str(self):
        log = SyncLog.objects.create(
            status='completed',
            summary='Test sync',
            records_created=10,
            records_updated=5
        )
        expected = f"Sync {log.start_time.strftime('%Y-%m-%d %H:%M')} - completed"
        self.assertEqual(str(log), expected)
