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
    current_user_id = int(get_jwt_identity())  # Convert string to int
    payload = request.get_json(silent=True) or {}

    public_key_pem = payload.get("public_key")
    algorithm = payload.get("algorithm", "ECDH")

    if not public_key_pem:
        return jsonify({"error": "public_key required"}), HTTPStatus.BAD_REQUEST

    # AGGRESSIVE cleaning - use character code filtering to be absolutely sure
    import re
    
    # Remove PEM headers/footers
    cleaned_key = re.sub(r'-----BEGIN[^-]*-----', '', public_key_pem, flags=re.IGNORECASE)
    cleaned_key = re.sub(r'-----END[^-]*-----', '', cleaned_key, flags=re.IGNORECASE)
    
    # Use character code filtering to remove ALL invalid characters
    # This is more reliable than regex
    cleaned_key = ''.join(char for char in cleaned_key if (
        ord('A') <= ord(char) <= ord('Z') or  # A-Z
        ord('a') <= ord(char) <= ord('z') or  # a-z
        ord('0') <= ord(char) <= ord('9') or  # 0-9
        char == '+' or
        char == '/' or
        char == '='
    ))
    
    # Validate it's proper base64
    if not cleaned_key or not re.match(r'^[A-Za-z0-9+/]+={0,2}$', cleaned_key):
        return jsonify({"error": "invalid public key format - contains non-base64 characters"}), HTTPStatus.BAD_REQUEST
    
    # Add padding if needed
    remainder = len(cleaned_key) % 4
    if remainder != 0:
        cleaned_key += '=' * (4 - remainder)
    
    # Reconstruct clean PEM format with proper line breaks
    public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{cleaned_key}\n-----END PUBLIC KEY-----"
    
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


@keys_bp.get("/email/<email>")
@jwt_required()
def get_public_key_by_email(email: str):
    """Retrieve public key for a user by email."""
    user = User.query.filter_by(email=email.lower(), is_active=True).first()
    if not user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    public_key = PublicKey.query.filter_by(user_id=user.id).first()
    if not public_key:
        return jsonify({"error": "public key not found for user"}), HTTPStatus.NOT_FOUND

    # Clean the key before returning it (in case database has corrupted data)
    import re
    cleaned_key = re.sub(r'-----BEGIN[^-]*-----', '', public_key.public_key_pem, flags=re.IGNORECASE)
    cleaned_key = re.sub(r'-----END[^-]*-----', '', cleaned_key, flags=re.IGNORECASE)
    cleaned_key = ''.join(char for char in cleaned_key if (
        ord('A') <= ord(char) <= ord('Z') or
        ord('a') <= ord(char) <= ord('z') or
        ord('0') <= ord(char) <= ord('9') or
        char == '+' or char == '/' or char == '='
    ))
    remainder = len(cleaned_key) % 4
    if remainder != 0:
        cleaned_key += '=' * (4 - remainder)
    clean_pem = f"-----BEGIN PUBLIC KEY-----\n{cleaned_key}\n-----END PUBLIC KEY-----"

    return jsonify(
        {
            "email": user.email,
            "public_key": clean_pem,
            "fingerprint": public_key.fingerprint,
            "algorithm": public_key.algorithm,
            "created_at": public_key.created_at.isoformat(),
        }
    ), HTTPStatus.OK


@keys_bp.get("/me")
@jwt_required()
def get_my_public_key():
    """Get current user's public key."""
    current_user_id = int(get_jwt_identity())  # Convert string to int
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

