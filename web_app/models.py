from django.db import models
from django.contrib.auth.models import AbstractUser

from django.db import models
from django.contrib.auth.models import AbstractUser

class Movie(models.Model):
    title = models.CharField(max_length=255, unique=True)
    synopsis = models.TextField()
    year = models.IntegerField()
    genre_id = models.IntegerField()
    director_id = models.IntegerField()
    rating = models.FloatField()
    language_id = models.IntegerField()
    country_id = models.IntegerField()
    age_rating_id = models.IntegerField()
    expires_at = models.DateTimeField()
    def __str__(self):
        return self.title

class Series(models.Model):
    ...

class Director(models.Model):
    name = models.CharField(max_length=255, unique=True)
    birth_date = models.DateField()
    country = models.CharField(max_length=255)
    def __str__(self):
        return self.name

class Genre(models.Model):
    genre = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.genre

class AgeRating(models.Model):
    age_rating = models.CharField(max_length=255, unique=True)
    age = models.IntegerField()
    def __str__(self):
        return self.age_rating

class CustomUser(AbstractUser):
    favorite_movies = models.ManyToManyField(Movie, blank=True)

    def __str__(self):
        return self.username

class SyncLog(models.Model):
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50)
    summary = models.TextField()