from django.db import models
from django.contrib.auth.models import AbstractUser


class API(models.Model):
    port = models.IntegerField(unique=True)

    def __str__(self):
        return f"API on port {self.port}"


class Director(models.Model):
    director_id = models.IntegerField()
    api = models.ForeignKey(API, on_delete=models.CASCADE, related_name='directors')
    name = models.CharField(max_length=255)
    birth_date = models.DateTimeField()
    country = models.CharField(max_length=255)

    class Meta:
        unique_together = ('director_id', 'api')

    def __str__(self):
        return self.name


class Genre(models.Model):
    genre_id = models.IntegerField()
    api = models.ForeignKey(API, on_delete=models.CASCADE, related_name='genres')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('genre_id', 'api')

    def __str__(self):
        return self.name


class AgeRating(models.Model):
    age_rating_id = models.IntegerField()
    api = models.ForeignKey(API, on_delete=models.CASCADE, related_name='age_ratings')
    description = models.CharField(max_length=255)
    age = models.IntegerField()

    class Meta:
        unique_together = ('age_rating_id', 'api')

    def __str__(self):
        return self.description


class Movie(models.Model):
    movie_id = models.IntegerField()
    age_rating = models.ForeignKey(AgeRating, on_delete=models.SET_NULL, blank=True, null=True)
    director = models.ForeignKey(Director, on_delete=models.SET_NULL, blank=True, null=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, blank=True, null=True)
    api = models.ForeignKey(API, blank=True, null=True, on_delete=models.SET_NULL)

    title = models.CharField(max_length=255)
    synopsis = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('movie_id', 'api')

    def __str__(self):
        return self.title

    def get_similar_by_genre(self, limit=4):
        if not self.genre:
            return Movie.objects.none()
        return Movie.objects.filter(genre=self.genre).exclude(id=self.id).order_by('?')[:limit]


class CustomUser(AbstractUser):
    favorite_movies = models.ManyToManyField(Movie, blank=True)

    def __str__(self):
        return self.username


class SyncLog(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50)
    summary = models.TextField()
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)

    def __str__(self):
        return f"Sync {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.status}"