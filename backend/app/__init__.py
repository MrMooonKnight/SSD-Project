"""Application factory for the VibeChat secure relay."""

from __future__ import annotations

from flask import Flask

from .config import load_config
from .extensions import cors, db, jwt, limiter, socketio
from .models import Contact, Message, PublicKey, User
from .routes.auth import auth_bp
from .routes.contacts import contacts_bp
from .routes.frontend import frontend_bp
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
    
    # CRITICAL: Ensure JWT_SECRET_KEY matches SECRET_KEY for token creation/validation
    # Flask-JWT-Extended uses JWT_SECRET_KEY if set, otherwise falls back to SECRET_KEY
    # We want them to be the same to avoid token validation failures
    if not app.config.get("JWT_SECRET_KEY") or app.config["JWT_SECRET_KEY"] == "change-jwt-secret-in-production":
        app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    
    # Double-check they match (this must happen BEFORE jwt.init_app())
    if app.config.get("JWT_SECRET_KEY") != app.config.get("SECRET_KEY"):
        # Force them to match - use SECRET_KEY as the source of truth
        app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
    
    # Configure JWT to look for tokens in Authorization header (default, but explicit is better)
    app.config.setdefault("JWT_TOKEN_LOCATION", ["headers"])
    app.config.setdefault("JWT_HEADER_NAME", "Authorization")
    app.config.setdefault("JWT_HEADER_TYPE", "Bearer")
    app.config.setdefault("JWT_ALGORITHM", "HS256")
    
    # Debug: Print JWT config (remove in production)
    if app.config.get("DEBUG"):
        print(f"JWT_SECRET_KEY set: {bool(app.config.get('JWT_SECRET_KEY'))}")
        print(f"SECRET_KEY set: {bool(app.config.get('SECRET_KEY'))}")
        print(f"JWT_SECRET_KEY == SECRET_KEY: {app.config.get('JWT_SECRET_KEY') == app.config.get('SECRET_KEY')}")
    
    # Initialize JWT - this reads JWT_SECRET_KEY from app.config
    jwt.init_app(app)
    
    # Register JWT error handlers
    from flask import jsonify
    from http import HTTPStatus
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "token has expired"}), HTTPStatus.UNAUTHORIZED
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        import traceback
        error_msg = str(error)
        if app.config.get("DEBUG"):
            print(f"Invalid token error: {error_msg}")
            traceback.print_exc()
        return jsonify({"error": f"invalid token: {error_msg}"}), HTTPStatus.UNAUTHORIZED
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        error_msg = str(error)
        if app.config.get("DEBUG"):
            print(f"Unauthorized error: {error_msg}")
        return jsonify({"error": f"authorization required: {error_msg}"}), HTTPStatus.UNAUTHORIZED
    # Configure Socket.IO CORS - ensure localhost is always allowed for development
    # Socket.IO needs explicit origin matching, so we'll use "*" for development
    # In production, you should specify exact origins
    socketio_cors = "*"  # Allow all origins for development (change in production)
    
    # Initialize socketio with the app
    socketio.init_app(app, cors_allowed_origins=socketio_cors)

    register_security_headers(app)

    # Register blueprints
    app.register_blueprint(frontend_bp)
    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(contacts_bp, url_prefix="/api/contacts")
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


