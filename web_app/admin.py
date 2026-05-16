from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import SyncLog, API, Contingut, Movie, Series, Director, Genre, AgeRating, CustomUser, UserProfile, Valoracio, Preferits


@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    list_display = ('port', 'name')
    fields = ('port', 'name')


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'status_visual', 'records_created', 'records_updated')
    list_filter = ('status', 'start_time')
    readonly_fields = ('start_time', 'end_time', 'status', 'summary', 'records_created', 'records_updated')

    def status_visual(self, obj):
        if obj.status.lower() == 'error':
            return mark_safe('<span style="color: red; font-weight: bold;">ERROR</span>')
        elif obj.status.lower() == 'success':
            return mark_safe('<span style="color: green; font-weight: bold;">SUCCESS</span>')
        elif obj.status.lower() == 'running':
            return mark_safe('<span style="color: orange; font-weight: bold;">RUNNING</span>')
        return obj.status

    status_visual.short_description = 'Status'


@admin.register(Contingut)
class ContingutAdmin(admin.ModelAdmin):
    list_display = ('titol', 'data_estrena', 'genere', 'director', 'age_rating', 'display_apis')
    list_filter = ('apis', 'genere', 'director', 'age_rating')
    search_fields = ('titol',)

    def display_apis(self, obj):
        return ", ".join([api.name or str(api.port) for api in obj.apis.all()])
    display_apis.short_description = 'Plataformas'


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'genre_name', 'director_name', 'api_name')
    list_filter = ('contingut__apis', 'contingut__genere', 'contingut__director')
    search_fields = ('contingut__titol',)

    def title(self, obj):
        return obj.contingut.titol
    def year(self, obj):
        return obj.contingut.data_estrena
    def genre_name(self, obj):
        return obj.contingut.genere.name if obj.contingut.genere else '-'
    def director_name(self, obj):
        return obj.contingut.director.name if obj.contingut.director else '-'
    
    def api_name(self, obj):
        return ", ".join([api.name or str(api.port) for api in obj.contingut.apis.all()]) if obj.contingut.apis.exists() else '-'


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'num_temporades', 'genre_name', 'director_name')
    list_filter = ('contingut__apis', 'contingut__genere', 'contingut__director')
    search_fields = ('contingut__titol',)

    def title(self, obj):
        return obj.contingut.titol
    def year(self, obj):
        return obj.contingut.data_estrena
    def genre_name(self, obj):
        return obj.contingut.genere.name if obj.contingut.genere else '-'
    def director_name(self, obj):
        return obj.contingut.director.name if obj.contingut.director else '-'
    
    def api_name(self, obj):
        return ", ".join([api.name or str(api.port) for api in obj.contingut.apis.all()]) if obj.contingut.apis.exists() else '-'


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'director_id', 'api', 'country', 'birth_date')
    list_filter = ('api',)
    search_fields = ('name',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'genre_id', 'api')
    list_filter = ('api',)
    search_fields = ('name',)


@admin.register(AgeRating)
class AgeRatingAdmin(admin.ModelAdmin):
    list_display = ('codi', 'age', 'age_rating_id', 'api')
    list_filter = ('api',)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'type', 'is_staff')
    list_filter = ('type', 'is_staff', 'is_active')
    search_fields = ('username', 'email')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferits_count')
    search_fields = ('user__username',)

    def preferits_count(self, obj):
        return obj.preferits.count()


@admin.register(Valoracio)
class ValoracioAdmin(admin.ModelAdmin):
    list_display = ('user', 'contingut_titol', 'puntuacio', 'creada_a')
    list_filter = ('puntuacio',)
    search_fields = ('user__username', 'contingut__titol')

    def contingut_titol(self, obj):
        return obj.contingut.titol


@admin.register(Preferits)
class PreferitsAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'contingut_titol', 'afegit_a')
    list_filter = ('afegit_a',)
    search_fields = ('user_profile__user__username', 'contingut__titol')

    def contingut_titol(self, obj):
        return obj.contingut.titol
