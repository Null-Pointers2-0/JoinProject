import hashlib
from django.db.models import Count, Q
from web_app.models import Contingut, Visualitzacio, Preferits, API, Genre, AgeRating, Director
from django.utils import timezone

def get_content_analytics(start_date=None, end_date=None, platform_ids=None):
    # 1. FIX ARQUITECTURA: Cambiamos 'api' por 'apis' y usamos prefetch_related
    queryset = Contingut.objects.select_related('genere', 'age_rating', 'director').prefetch_related('apis')

    if start_date and not end_date:
        end_date = timezone.now().date()

    # Filtros base del contenido (ej. filtrar por plataformas)
    base_filters = Q()
    if platform_ids:
        base_filters &= Q(apis__in=platform_ids)

    # 2. FIX ANALÍTICAS: Los filtros de fecha van dentro de la agregación, no en el WHERE global
    view_filters = Q()
    fav_filters = Q()
    
    if start_date and end_date:
        view_filters = Q(visualitzacions__data_visualitzacio__range=(start_date, end_date))
        fav_filters = Q(preferits__afegit_a__range=(start_date, end_date))
    elif end_date:  
        view_filters = Q(visualitzacions__data_visualitzacio__lte=end_date)
        fav_filters = Q(preferits__afegit_a__lte=end_date)

    # 3. FIX DUPLICADOS: .distinct() es vital al filtrar por ManyToMany (apis__in)
    analytics_data = queryset.filter(base_filters).distinct().annotate(
        total_views=Count('visualitzacions', filter=view_filters, distinct=True),
        total_favorites=Count('preferits', filter=fav_filters, distinct=True)
    )

    results = []
    for item in analytics_data:
        # 4. FIX PRESENTACIÓN: Formateamos las múltiples plataformas en un string
        plataformas = ", ".join([api.name or str(api.port) for api in item.apis.all()]) if item.apis.exists() else 'N/A'
        
        results.append(
            {
                'title': item.titol,
                'genre': item.genere.name if item.genere else 'N/A',
                'age_rating': item.age_rating.codi if item.age_rating else 'N/A',
                'year': item.data_estrena,
                'director': item.director.name if item.director else 'N/A',
                'platform': plataformas,
                'views': item.total_views,
                'favorites': item.total_favorites,
            }
        )
    return results

def format_analytics_for_csv(data_list, is_b2b_report=False):
    formatted_data = []
    for row in data_list:
        if is_b2b_report:
            if 'username' in row and row['username']:
                user_hash = hashlib.sha256(row['username'].encode()).hexdigest()[:10]
                row['username'] = f"USER_{user_hash}"
            
            row.pop('email', None)
            row.pop('id_address', None)
        
        formatted_data.append(row)
        
    return formatted_data

def get_genre_distribution(start_date=None, end_date=None, platform_ids=None):
    if start_date and not end_date:
        end_date = timezone.now().date()

    base_filters = Q()
    if platform_ids:
        base_filters &= Q(apis__in=platform_ids)

    view_filters = Q()
    if start_date and end_date:
        view_filters = Q(visualitzacions__data_visualitzacio__range=(start_date, end_date))
    elif end_date:
        view_filters = Q(visualitzacions__data_visualitzacio__lte=end_date)

    # Añadimos el distinct() al sub-query para evitar multiplicar cálculos
    data = Genre.objects.filter(contingut__in=Contingut.objects.filter(base_filters).distinct()).annotate(
        total_views=Count('contingut__visualitzacions', filter=Q(contingut__in=Contingut.objects.filter(view_filters)), distinct=True)
    ).order_by('-total_views')

    return {
        'labels': [g.name for g in data],
        'values': [g.total_views for g in data]
    }

def get_age_rating_distribution(start_date=None, end_date=None, platform_ids=None):
    if start_date and not end_date:
        end_date = timezone.now().date()
        
    base_filters = Q()
    if platform_ids:
        base_filters &= Q(apis__in=platform_ids)

    view_filters = Q()
    if start_date and end_date:
        view_filters = Q(visualitzacions__data_visualitzacio__range=(start_date, end_date))
    elif end_date:
        view_filters = Q(visualitzacions__data_visualitzacio__lte=end_date)

    data = AgeRating.objects.filter(contingut__in=Contingut.objects.filter(base_filters).distinct()).annotate(
        total_views=Count('contingut__visualitzacions', filter=Q(contingut__in=Contingut.objects.filter(view_filters)), distinct=True)
    ).order_by('-total_views')

    return {
        'labels': [ar.codi for ar in data],
        'values': [ar.total_views for ar in data]
    }

def get_director_top_list(start_date=None, end_date=None, platform_ids=None):
    if start_date and not end_date:
        end_date = timezone.now().date()

    base_filters = Q()
    if platform_ids:
        base_filters &= Q(apis__in=platform_ids)

    view_filters = Q()
    if start_date and end_date:
        view_filters = Q(visualitzacions__data_visualitzacio__range=(start_date, end_date))
    elif end_date:
        view_filters = Q(visualitzacions__data_visualitzacio__lte=end_date)

    data = Director.objects.filter(contingut__in=Contingut.objects.filter(base_filters).distinct()).annotate(
        total_views=Count('contingut__visualitzacions', filter=Q(contingut__in=Contingut.objects.filter(view_filters)), distinct=True)
    ).order_by('-total_views')[:10]

    return {
        'labels': [d.name for d in data],
        'values': [d.total_views for d in data]
    }