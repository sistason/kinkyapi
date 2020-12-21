echo "Make migrations"
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate

echo "Start Gunicorn"
gunicorn kinkyapi.wsgi:application --bind 0.0.0.0:8080
