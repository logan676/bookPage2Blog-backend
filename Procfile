web: python manage.py migrate && gunicorn bookpost_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4
