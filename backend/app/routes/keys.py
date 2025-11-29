"""Public key management endpoints."""

from __future__ import annotations

from http import HTTPStatus
from hashlib import sha256

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db
from ..models import PublicKey, User

keys_bp = Blueprint("keys", __name__)


def compute_fingerprint(public_key_pem: str) -> str:
    """Compute SHA-256 fingerprint of public key."""
    return sha256(public_key_pem.encode()).hexdigest()


@keys_bp.post("/upload")
@jwt_required()
def upload_public_key():
    """Upload or update user's public key."""
    current_user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    public_key_pem = payload.get("public_key")
    algorithm = payload.get("algorithm", "Ed25519")

    if not public_key_pem:
        return jsonify({"error": "public_key required"}), HTTPStatus.BAD_REQUEST

    fingerprint = compute_fingerprint(public_key_pem)

    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    # Check if public key already exists
    existing_key = PublicKey.query.filter_by(user_id=current_user_id).first()

    if existing_key:
        # Update existing key
        existing_key.public_key_pem = public_key_pem
        existing_key.fingerprint = fingerprint
        existing_key.algorithm = algorithm
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "public key updated",
                    "fingerprint": fingerprint,
                    "algorithm": algorithm,
                }
            ),
            HTTPStatus.OK,
        )

    # Create new public key
    new_key = PublicKey(
        user_id=current_user_id,
        public_key_pem=public_key_pem,
        fingerprint=fingerprint,
        algorithm=algorithm,
    )
    db.session.add(new_key)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "public key uploaded",
                "fingerprint": fingerprint,
                "algorithm": algorithm,
            }
        ),
        HTTPStatus.CREATED,
    )


@keys_bp.get("/<username>")
@jwt_required()
def get_public_key(username: str):
    """Retrieve public key for a user by username."""
    user = User.query.filter_by(username=username, is_active=True).first()
    if not user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    public_key = PublicKey.query.filter_by(user_id=user.id).first()
    if not public_key:
        return jsonify({"error": "public key not found for user"}), HTTPStatus.NOT_FOUND

    return jsonify(
        {
            "username": username,
            "public_key": public_key.public_key_pem,
            "fingerprint": public_key.fingerprint,
            "algorithm": public_key.algorithm,
            "created_at": public_key.created_at.isoformat(),
        }
    ), HTTPStatus.OK


@keys_bp.get("/me")
@jwt_required()
def get_my_public_key():
    """Get current user's public key."""
    current_user_id = get_jwt_identity()
    public_key = PublicKey.query.filter_by(user_id=current_user_id).first()

    if not public_key:
        return jsonify({"error": "public key not found"}), HTTPStatus.NOT_FOUND

    return jsonify(
        {
            "public_key": public_key.public_key_pem,
            "fingerprint": public_key.fingerprint,
            "algorithm": public_key.algorithm,
            "created_at": public_key.created_at.isoformat(),
            "updated_at": public_key.updated_at.isoformat(),
        }
    ), HTTPStatus.OK

