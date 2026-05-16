from django.db import models
from django.contrib.auth.models import AbstractUser
from web import settings


class UserType(models.TextChoices):
    STAFF = 'Staff', 'Staff'
    STAFF_ADMIN = 'Staff Admin', 'Staff Admin'
    ADMIN = 'Admin', 'Admin'
    CONSUMER = 'Consumer', 'Consumer'

class API(models.Model):
    port = models.IntegerField(unique=True)
    name = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return self.name if self.name else f"{self.port}"


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
    codi = models.CharField(max_length=10, verbose_name='Codi')
    age = models.IntegerField()

    class Meta:
        unique_together = ('age_rating_id', 'api')

    def __str__(self):
        return self.codi

    @property
    def description(self):
        return self.codi


class Contingut(models.Model):
    titol = models.CharField(max_length=255, verbose_name='Títol', db_index=True)
    data_estrena = models.IntegerField(blank=True, null=True, verbose_name='Any d\'estrena')
    expires_at = models.DateTimeField(blank=True, null=True)
    director = models.ForeignKey(Director, on_delete=models.SET_NULL, blank=True, null=True)
    genere = models.ForeignKey(Genre, on_delete=models.SET_NULL, blank=True, null=True)
    age_rating = models.ForeignKey(AgeRating, on_delete=models.SET_NULL, blank=True, null=True)
    apis = models.ManyToManyField(API, blank=True, related_name='continguts')

    poster_path = models.TextField(blank=True, null=True)
    synopsis = models.TextField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name = 'Contingut'
        verbose_name_plural = 'Continguts'

    def __str__(self):
        return self.titol


class Movie(models.Model):
    contingut = models.OneToOneField(Contingut, on_delete=models.CASCADE, related_name='movie')

    class Meta:
        verbose_name = 'Pel·lícula'
        verbose_name_plural = 'Pel·lícules'

    def __str__(self):
        return self.contingut.titol

    @property
    def title(self):
        return self.contingut.titol

    @property
    def year(self):
        return self.contingut.data_estrena

    @property
    def genre(self):
        return self.contingut.genere

    @property
    def director(self):
        return self.contingut.director

    @property
    def age_rating(self):
        return self.contingut.age_rating

    @property
    def synopsis(self):
        return self.contingut.synopsis

    @property
    def rating(self):
        return self.contingut.rating

    @property
    def poster_path(self):
        return self.contingut.poster_path

    def get_similar_by_genre(self, limit=4):
        if not self.contingut.genere:
            return Movie.objects.none()

        return Movie.objects.filter(
            contingut__genere=self.contingut.genere
        ).exclude(id=self.id).order_by('?')[:limit]

class Series(models.Model):
    contingut = models.OneToOneField(Contingut, on_delete=models.CASCADE, related_name='series')
    num_temporades = models.IntegerField(blank=True, null=True, verbose_name='Nombre de temporades')

    class Meta:
        verbose_name = 'Sèrie'
        verbose_name_plural = 'Sèries'

    def __str__(self):
        return self.contingut.titol

    @property
    def title(self):
        return self.contingut.titol

    @property
    def year(self):
        return self.contingut.data_estrena

    @property
    def start_year(self):
        return self.contingut.data_estrena

    @property
    def end_year(self):
        return None

    @property
    def genre(self):
        return self.contingut.genere

    @property
    def director(self):
        return self.contingut.director

    @property
    def age_rating(self):
        return self.contingut.age_rating

    @property
    def synopsis(self):
        return self.contingut.synopsis

    @property
    def rating(self):
        return self.contingut.rating

    @property
    def total_seasons(self):
        return self.num_temporades

    @property
    def poster_path(self):
        return self.contingut.poster_path


class CustomUser(AbstractUser):
    """
    Extends the default Django user model to include additional profile attributes 
    like a custom avatar, user biography, and physical location.
    """
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(
        choices=UserType.choices,
        default=UserType.CONSUMER,
    )
    subscriptions = models.ManyToManyField('API', blank=True, related_name='subscribed_users')

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    preferits = models.ManyToManyField(Contingut, blank=True, through='Preferits')

    def __str__(self):
        return f"Perfil de {self.user.username}"


class Preferits(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='preferits_set')
    contingut = models.ForeignKey(Contingut, on_delete=models.CASCADE)
    afegit_a = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_profile', 'contingut')
        verbose_name = 'Preferit'
        verbose_name_plural = 'Preferits'

    def __str__(self):
        return f"{self.user_profile.user.username} -> {self.contingut.titol}"


class Valoracio(models.Model):
    puntuacio = models.IntegerField()
    comentari = models.TextField(blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='valoracions')
    contingut = models.ForeignKey(Contingut, on_delete=models.CASCADE, related_name='valoracions')
    creada_a = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Valoració'
        verbose_name_plural = 'Valoracions'

    def __str__(self):
        return f"{self.user.username} -> {self.contingut.titol} ({self.puntuacio}/5)"


class Visualitzacio(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='visualitzacions')
    contingut = models.ForeignKey(Contingut, on_delete=models.CASCADE, related_name='visualitzacions')
    data_visualitzacio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Visualització'
        verbose_name_plural = 'Visualitzacions'

    def __str__(self):
        user_str = self.user.username if self.user else "Anònim"
        return f"{user_str} -> {self.contingut.titol} ({self.data_visualitzacio})"


class SyncLog(models.Model):

    """
    Records the operational status and statistical summary of background synchronization 
    processes, tracking the total number of created and updated database records.
    """
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50)
    summary = models.TextField()
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)

    def __str__(self):
        return f"Sync {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.status}"
