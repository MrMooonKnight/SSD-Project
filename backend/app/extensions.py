"""Extension instances shared across the Flask app."""

from __future__ import annotations

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

from .models import db

cors = CORS()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


