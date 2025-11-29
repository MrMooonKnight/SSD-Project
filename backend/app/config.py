"""Configuration utilities for the Flask application."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dynaconf import Dynaconf

BASE_DIR = Path(__file__).resolve().parents[1]
settings = Dynaconf(
    envvar_prefix="VIBE",
    env_switcher="VIBE_ENV",
    environments=True,
    load_dotenv=True,
    settings_files=[],
)

DEFAULT_CONFIG: dict[str, Any] = {
    "SECRET_KEY": "change-me-in-production",
    "JWT_SECRET_KEY": "change-jwt-secret-in-production",
    "JWT_ACCESS_TOKEN_EXPIRES": 3600,  # 1 hour
    "JWT_REFRESH_TOKEN_EXPIRES": 86400,  # 24 hours
    "ENV": "development",
    "DEBUG": False,
    "TESTING": False,
    "JSON_SORT_KEYS": False,
    "PREFERRED_URL_SCHEME": "https",
    "SQLALCHEMY_DATABASE_URI": "sqlite:///vibechat.db",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "SQLALCHEMY_ECHO": False,
    "RATELIMIT_DEFAULT": "20/minute",
    "RATELIMIT_STORAGE_URI": "memory://",
    "CORS_ORIGINS": ["http://localhost:5173", "https://localhost:5173"],
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Strict",
    "SESSION_COOKIE_SECURE": True,
    "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,  # 5 MB placeholder
}


def _coerce_list(value: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def load_config(app, config_name: str | None = None) -> None:
    """Attach configuration to the Flask app."""
    app.config.from_mapping(DEFAULT_CONFIG)

    env_config = settings.get(config_name or "default") if config_name else {}
    if isinstance(env_config, Mapping):
        app.config.update(env_config)

    dynamic_overrides = settings.as_dict()
    if dynamic_overrides:
        app.config.update(dynamic_overrides)

    secret = settings.get("secret_key")
    if secret:
        app.config["SECRET_KEY"] = secret

    cors_origins = settings.get("cors_origins")
    if cors_origins:
        app.config["CORS_ORIGINS"] = _coerce_list(cors_origins)

