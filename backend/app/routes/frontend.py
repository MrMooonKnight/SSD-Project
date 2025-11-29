"""Frontend routes for serving HTML pages."""

from __future__ import annotations

from flask import Blueprint, render_template, session
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def index():
    """Home page - redirects to login or chat."""
    return render_template("index.html")


@frontend_bp.route("/login")
def login_page():
    """Login page."""
    return render_template("login.html")


@frontend_bp.route("/register")
def register_page():
    """Registration page."""
    return render_template("register.html")


@frontend_bp.route("/chat")
def chat_page():
    """Chat interface page."""
    return render_template("chat.html")

