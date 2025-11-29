"""Contact management endpoints."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Contact, User

contacts_bp = Blueprint("contacts", __name__)


@contacts_bp.post("/add")
@jwt_required()
def add_contact():
    """Add a contact by email."""
    current_user_id = int(get_jwt_identity())  # Convert string to int
    payload = request.get_json(silent=True) or {}
    contact_email = payload.get("email", "").strip().lower()

    if not contact_email:
        return jsonify({"error": "email required"}), HTTPStatus.BAD_REQUEST

    # Find contact user
    contact_user = User.query.filter_by(email=contact_email, is_active=True).first()
    if not contact_user:
        return jsonify({"error": "user not found"}), HTTPStatus.NOT_FOUND

    if contact_user.id == current_user_id:
        return jsonify({"error": "cannot add yourself as contact"}), HTTPStatus.BAD_REQUEST

    # Check if contact already exists
    existing_contact = Contact.query.filter_by(user_id=current_user_id, contact_id=contact_user.id).first()
    if existing_contact:
        return jsonify({"error": "contact already exists"}), HTTPStatus.CONFLICT

    # Create contact with error handling for race conditions
    try:
        new_contact = Contact(user_id=current_user_id, contact_id=contact_user.id)
        db.session.add(new_contact)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # Contact was added between check and commit (race condition)
        return jsonify({"error": "contact already exists"}), HTTPStatus.CONFLICT

    return (
        jsonify(
            {
                "message": "contact added",
                "contact_id": contact_user.id,
                "email": contact_user.email,
                "display_name": contact_user.display_name,
            }
        ),
        HTTPStatus.CREATED,
    )


@contacts_bp.get("/list")
@jwt_required()
def list_contacts():
    """Get list of user's contacts."""
    current_user_id = int(get_jwt_identity())  # Convert string to int

    contacts = Contact.query.filter_by(user_id=current_user_id).all()

    return jsonify(
        {
            "contacts": [
                {
                    "contact_id": contact.contact.id,
                    "email": contact.contact.email,
                    "display_name": contact.contact.display_name,
                    "created_at": contact.created_at.isoformat(),
                }
                for contact in contacts
            ],
            "count": len(contacts),
        }
    ), HTTPStatus.OK


@contacts_bp.delete("/<int:contact_id>")
@jwt_required()
def remove_contact(contact_id: int):
    """Remove a contact."""
    current_user_id = int(get_jwt_identity())  # Convert string to int

    contact = Contact.query.filter_by(user_id=current_user_id, contact_id=contact_id).first()
    if not contact:
        return jsonify({"error": "contact not found"}), HTTPStatus.NOT_FOUND

    db.session.delete(contact)
    db.session.commit()

    return jsonify({"message": "contact removed"}), HTTPStatus.OK

