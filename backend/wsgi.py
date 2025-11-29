"""WSGI entry point for production servers."""

from app import create_app
from app.extensions import socketio

app = create_app()

# Export for Gunicorn
application = app

