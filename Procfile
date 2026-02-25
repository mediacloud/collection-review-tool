web: cd backend && gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 3
release: cd backend && flask --app app:create_app db upgrade

