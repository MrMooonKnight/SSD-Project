"""Authentication blueprint with JWT support."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """Register a new user account."""
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    password = payload.get("password")
    display_name = payload.get("display_name", "").strip() or None

    if not username or not password:
        return jsonify({"error": "username and password required"}), HTTPStatus.BAD_REQUEST

    if len(username) < 3 or len(username) > 80:
        return jsonify({"error": "username must be between 3 and 80 characters"}), HTTPStatus.BAD_REQUEST

    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), HTTPStatus.BAD_REQUEST

    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "username already taken"}), HTTPStatus.CONFLICT

    # Create new user
    password_hash = generate_password_hash(password)
    new_user = User(
        username=username,
        password_hash=password_hash,
        display_name=display_name,
    )
    db.session.add(new_user)
    db.session.commit()

    # Generate tokens
    access_token = create_access_token(identity=new_user.id)
    refresh_token = create_refresh_token(identity=new_user.id)

    return (
        jsonify(
            {
                "message": "user registered successfully",
                "user_id": new_user.id,
                "username": new_user.username,
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
    username = payload.get("username", "").strip()
    password = payload.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), HTTPStatus.BAD_REQUEST

    # Find user
    user = User.query.filter_by(username=username, is_active=True).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), HTTPStatus.UNAUTHORIZED

    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify(
        {
            "message": "login successful",
            "user_id": user.id,
            "username": user.username,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    ), HTTPStatus.OK


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id, is_active=True).first()

    if not user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    new_access_token = create_access_token(identity=user.id)
    return jsonify({"access_token": new_access_token}), HTTPStatus.OK


@auth_bp.get("/me")
@jwt_required()
def get_current_user():
    """Get current authenticated user information."""
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id, is_active=True).first()

    if not user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    return jsonify(
        {
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "created_at": user.created_at.isoformat(),
        }
    ), HTTPStatus.OK


