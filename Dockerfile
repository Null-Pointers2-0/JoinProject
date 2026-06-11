FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD python3 manage.py migrate --fake-initial && python3 manage.py load_municipalities && gunicorn web.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 90