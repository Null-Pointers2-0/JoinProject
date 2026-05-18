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

def get_content_analytics(start_date=None, end_date=None, plataform_id=None):
    queryset = Contingut.objects.select_related('genere', 'age_rating', 'api', 'director')

    if start_date and not end_date:
        end_date = timezone.now().date()

    filters = Q()
    if start_date and end_date:
        filters &= Q(visualitzacions__data_visualitzacio__range=(start_date,end_date))
        filters &= Q(preferits__afegit_a__range=(start_date,end_date))
    elif end_date:  
        filters &= Q(visualitzacions__data_visualitzacio__lte=end_date)
        filters &= Q(preferits__afegit_a__lte=end_date)

    if plataform_id:
        filters &= Q(api__id=plataform_id)

    analytics_data = queryset.filter(filters).annotate(
        total_views=Count('visualitzacions', distinct=True),
        total_favorites=Count('preferits', distinct=True)
    )

    results = []

    for item in analytics_data:
        results.append(
            {
                'title': item.titol,
                'genre': item.genere.name if item.genere else 'N/A',
                'age_rating': item.age_rating.codi if item.age_rating else 'N/A',
                'year': item.data_estrena,
                'director': item.director.name if item.director else 'N/A',
                'platform': item.api.name if item.api else 'N/A',
                'views': item.total_views,
                'favorites': item.total_favorites,
            }
        )
    return results

def format_analytics_for_csv (data_list, is_b2b_report = False):
    formatted_data = []
    for row in data_list:
        safe_row = _strip_pii(row)

        if is_b2b_report:
            for field in GDPR_ANONYMIZE_FIELDS & row.keys():
                safe_row[field] = anonymize_user_id(row[field])
        
        formatted_data.append(safe_row)
        
    return formatted_data

def get_genre_distribution(start_date=None, end_date=None, platform_id=None):
    if start_date and not end_date:
        end_date = timezone.now().date()

    filters = Q()
    if start_date and end_date:
        filters &= Q(visualitzacions__data_visualitzacio__range=(start_date,end_date))
    elif end_date:
        filters &= Q(visualitzacions__data_visualitzacio__lte=end_date)
    if platform_id:
        filters &= Q(api__id=platform_id)

    data = Genre.objects.filter(contingut__in=Contingut.objects.filter(filters)).annotate(
        total_views=Count('contingut__visualitzacions', distinct=True)
    ).order_by('-total_views')

    return {
        'labels': [g.name for g in data],
        'values': [g.total_views for g in data]
    }

def get_age_rating_distribution(start_date=None, end_date=None, platform_id=None):
    if start_date and not end_date:
        end_date = timezone.now().date()
        
    filters = Q()
    if start_date and end_date:
        filters &= Q(visualitzacions__data_visualitzacio__range=(start_date,end_date))
    elif end_date:
        filters &= Q(visualitzacions__data_visualitzacio__lte=end_date)

    if platform_id:
        filters &= Q(api__id=platform_id)

    data = AgeRating.objects.filter(contingut__in=Contingut.objects.filter(filters)).annotate(
        total_views=Count('contingut__visualitzacions', distinct=True)
    ).order_by('-total_views')

    return {
        'labels': [ar.codi for ar in data],
        'values': [ar.total_views for ar in data]
    }

def get_director_top_list(start_date=None, end_date=None, platform_id=None):
    if start_date and not end_date:
        end_date = timezone.now().date()

    filters = Q()
    if start_date and end_date:
        filters &= Q(visualitzacions__data_visualitzacio__range=(start_date,end_date))
    elif end_date:
        filters &= Q(visualitzacions__data_visualitzacio__lte=end_date)

    if platform_id:
        filters &= Q(api__id=platform_id)

    data = Director.objects.filter(contingut__in=Contingut.objects.filter(filters)).annotate(
        total_views=Count('contingut__visualitzacions', distinct=True)
    ).order_by('-total_views')[:10]

    return {
        'labels': [d.name for d in data],
        'values': [d.total_views for d in data]
    }
