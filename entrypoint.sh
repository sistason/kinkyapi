echo "Make migrations"
python manage.py collectstatic --noinput
python manage.py makemigrations
if ! python manage.py migrate; then
    echo "Database problem!"
    exit 1
fi

echo "Start Gunicorn"
gunicorn kinkyapi.wsgi:application --bind 0.0.0.0:8080
