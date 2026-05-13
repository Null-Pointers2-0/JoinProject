FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD python3 -m pip install --no-cache-dir setuptools &&  python3 manage.py migrate --fake-initial && gunicorn web.wsgi:application --bind 0.0.0.0:${PORT:-8000}