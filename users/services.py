import hashlib
import hmac
import re
from django.db.models import Count, Q
from web_app.models import Contingut, Visualitzacio, Preferits, API, Genre, AgeRating, Director
from django.utils import timezone
from django.conf import settings

PII_COLUMNS = frozenset({
    'username', 'email', 'ip_address', 'id_address',
    'first_name', 'last_name', 'location', 'bio',
    'avatar', 'password',
})

GDPR_ANONYMIZE_FIELDS = frozenset({
    'username', 'email', 'first_name', 'last_name',
    'user_id', 'ip_address', 'id_address',
})

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

def anonymize_user_id(identifier, salt=None):
    salt = salt or settings.SECRET_KEY
    h = hmac.new(salt.encode(), str(identifier).encode(), hashlib.sha256)
    return f"UID_{h.hexdigest()[:12]}"

def _strip_pii(row):
    return {k: v for k, v in row.items() if k not in PII_COLUMNS}

def validate_gdpr_compliance(data_list, is_b2b_report=False):
    for row in data_list:
        for key, value in row.items():
            if key in PII_COLUMNS:
                if is_b2b_report and key in GDPR_ANONYMIZE_FIELDS and isinstance(value, str) and value.startswith('UID_'):
                    continue
                raise ValueError(f"GDPR violation: PII column '{key}' found in report data")
            if isinstance(value, str) and EMAIL_RE.search(value):
                raise ValueError(f"GDPR violation: email pattern found in field '{key}': {value}")
        if is_b2b_report:
            for field in GDPR_ANONYMIZE_FIELDS & row.keys():
                if not isinstance(row[field], str) or not row[field].startswith('UID_'):
                    raise ValueError(
                        f"GDPR violation: field '{field}' in B2B report is not anonymized: {row[field]}"
                    )

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
        safe_row = _strip_pii(row)

        if is_b2b_report:
            for field in GDPR_ANONYMIZE_FIELDS & row.keys():
                safe_row[field] = anonymize_user_id(row[field])
        
        formatted_data.append(safe_row)
        
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

def _base_view_filters(start_date=None, end_date=None, platform_ids=None):
    filters = Q()
    if start_date and end_date:
        filters &= Q(data_visualitzacio__range=(start_date, end_date))
    elif end_date:
        filters &= Q(data_visualitzacio__lte=end_date)
    if platform_ids:
        filters &= Q(api_id__in=platform_ids)
    return filters

def get_views_by_gender(start_date=None, end_date=None, platform_ids=None):
    filters = _base_view_filters(start_date, end_date, platform_ids)
    data = (
        Visualitzacio.objects.filter(filters)
        .exclude(user__gender__isnull=True)
        .values('user__gender')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    return {
        'labels': [d['user__gender'] for d in data],
        'values': [d['total'] for d in data],
    }

def get_views_by_age_range(start_date=None, end_date=None, platform_ids=None):
    filters = _base_view_filters(start_date, end_date, platform_ids)
    data = (
        Visualitzacio.objects.filter(filters)
        .exclude(user__age_range__isnull=True)
        .values('user__age_range')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    return {
        'labels': [d['user__age_range'] for d in data],
        'values': [d['total'] for d in data],
    }

def get_views_by_province(start_date=None, end_date=None, platform_ids=None):
    filters = _base_view_filters(start_date, end_date, platform_ids)
    data = (
        Visualitzacio.objects.filter(filters)
        .exclude(user__municipality__province__name__isnull=True)
        .values('user__municipality__province__name')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    labels = [d['user__municipality__province__name'] for d in data[:10]]
    values = [d['total'] for d in data[:10]]

    if len(data) > 10:
        others = sum(d['total'] for d in data[10:])
        labels.append('Others')
        values.append(others)

    return {'labels': labels, 'values': values}

def get_views_by_gender_age(start_date=None, end_date=None, platform_ids=None):
    filters = _base_view_filters(start_date, end_date, platform_ids)
    data = (
        Visualitzacio.objects.filter(filters)
        .exclude(user__gender__isnull=True)
        .exclude(user__age_range__isnull=True)
        .values('user__gender', 'user__age_range')
        .annotate(total=Count('id'))
        .order_by('user__gender', 'user__age_range')
    )

    age_order = ['<18', '18-30', '31-50', '>50']
    gender_order = ['Male', 'Female', 'Non-binary', 'Other']

    matrix = {}
    for d in data:
        g = d['user__gender']
        a = d['user__age_range']
        if g not in matrix:
            matrix[g] = {}
        matrix[g][a] = d['total']

    datasets = []
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    for i, age in enumerate(age_order):
        vals = [matrix.get(g, {}).get(age, 0) for g in gender_order if g in matrix]
        datasets.append({
            'label': age,
            'data': vals,
            'backgroundColor': colors[i % len(colors)],
        })

    present_genders = [g for g in gender_order if g in matrix]
    return {
        'labels': present_genders,
        'datasets': datasets,
    }