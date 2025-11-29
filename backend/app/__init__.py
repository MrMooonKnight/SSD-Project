"""Application factory for the VibeChat secure relay."""

from __future__ import annotations

from flask import Flask

from .config import load_config
from .extensions import cors, db, jwt, limiter, socketio
from .models import Message, PublicKey, User
from .routes.auth import auth_bp
from .routes.health import health_bp
from .routes.keys import keys_bp
from .routes.messages import messages_bp
from .security.headers import register_security_headers

# Import socketio handlers to register event handlers
from . import socketio_handlers  # noqa: F401


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    load_config(app, config_name)

    # Initialize extensions
    db.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=True,
    )
    limiter.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"))

    register_security_headers(app)

    # Register blueprints
    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(keys_bp, url_prefix="/api/keys")
    app.register_blueprint(messages_bp, url_prefix="/api/messages")

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.get("/api")
    def index():
        return {
            "service": "VibeChat Secure Relay",
            "status": "ok",
            "docs": "/api/health/live",
        }

    return app


