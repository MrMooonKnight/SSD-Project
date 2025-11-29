"""Authentication blueprint with JWT support."""

from __future__ import annotations

import re
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    return bool(EMAIL_REGEX.match(email))


@auth_bp.post("/register")
def register():
    """Register a new user account."""
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "").strip().lower()
    password = payload.get("password")
    display_name = payload.get("display_name", "").strip() or None

    if not email or not password:
        return jsonify({"error": "email and password required"}), HTTPStatus.BAD_REQUEST

    if not is_valid_email(email):
        return jsonify({"error": "invalid email format"}), HTTPStatus.BAD_REQUEST

    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), HTTPStatus.BAD_REQUEST

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "email already registered"}), HTTPStatus.CONFLICT

    # Create new user
    password_hash = generate_password_hash(password)
    new_user = User(
        email=email,
        password_hash=password_hash,
        display_name=display_name,
    )
    db.session.add(new_user)
    db.session.commit()

    # Generate tokens - identity must be a string for PyJWT 2.x
    access_token = create_access_token(identity=str(new_user.id))
    refresh_token = create_refresh_token(identity=str(new_user.id))

    return (
        jsonify(
            {
                "message": "user registered successfully",
                "user_id": new_user.id,
                "email": new_user.email,
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        ),
        HTTPStatus.CREATED,
    )


@auth_bp.post("/login")
def login():
    """Authenticate user and return JWT tokens."""
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "").strip().lower()
    password = payload.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), HTTPStatus.BAD_REQUEST

    # Find user
    user = User.query.filter_by(email=email, is_active=True).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), HTTPStatus.UNAUTHORIZED

    # Generate tokens - identity must be a string for PyJWT 2.x
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify(
        {
            "message": "login successful",
            "user_id": user.id,
            "email": user.email,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    ), HTTPStatus.OK


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    current_user_id = get_jwt_identity()
    # Convert string identity back to int for database query
    user = User.query.filter_by(id=int(current_user_id), is_active=True).first()

    if not user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    new_access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": new_access_token}), HTTPStatus.OK


@auth_bp.get("/me")
@jwt_required()
def get_current_user():
    """Get current authenticated user information."""
    current_user_id = get_jwt_identity()
    # Convert string identity back to int for database query
    user = User.query.filter_by(id=int(current_user_id), is_active=True).first()

    if not user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    return jsonify(
        {
            "user_id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "created_at": user.created_at.isoformat(),
        }
    ), HTTPStatus.OK


