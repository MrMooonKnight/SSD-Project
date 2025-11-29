"""Message relay endpoints for encrypted messages."""

from __future__ import annotations

from http import HTTPStatus
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import db, socketio
from ..models import Message, User

messages_bp = Blueprint("messages", __name__)


@messages_bp.post("/send")
@jwt_required()
def send_message():
    """Send an encrypted message to a recipient."""
    current_user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    recipient_username = payload.get("recipient")
    ciphertext = payload.get("ciphertext")
    nonce = payload.get("nonce")
    message_type = payload.get("message_type", "text")

    if not recipient_username or not ciphertext:
        return jsonify({"error": "recipient and ciphertext required"}), HTTPStatus.BAD_REQUEST

    recipient = User.query.filter_by(username=recipient_username, is_active=True).first()
    if not recipient:
        return jsonify({"error": "recipient not found"}), HTTPStatus.NOT_FOUND

    if recipient.id == current_user_id:
        return jsonify({"error": "cannot send message to yourself"}), HTTPStatus.BAD_REQUEST

    # Create message record
    message = Message(
        sender_id=current_user_id,
        recipient_id=recipient.id,
        ciphertext=ciphertext,
        nonce=nonce,
        message_type=message_type,
    )
    db.session.add(message)
    db.session.commit()

    # Emit via WebSocket for real-time delivery
    socketio.emit(
        "new_message",
        {
            "message_id": message.id,
            "sender_id": current_user_id,
            "recipient_id": recipient.id,
            "ciphertext": ciphertext,
            "nonce": nonce,
            "message_type": message_type,
            "created_at": message.created_at.isoformat(),
        },
        room=f"user_{recipient.id}",
    )

    return (
        jsonify(
            {
                "message": "message sent",
                "message_id": message.id,
                "created_at": message.created_at.isoformat(),
            }
        ),
        HTTPStatus.CREATED,
    )


@messages_bp.get("/inbox")
@jwt_required()
def get_inbox():
    """Retrieve received messages for current user."""
    current_user_id = get_jwt_identity()
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    messages = (
        Message.query.filter_by(recipient_id=current_user_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify(
        {
            "messages": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "sender_username": msg.sender.username,
                    "ciphertext": msg.ciphertext,
                    "nonce": msg.nonce,
                    "message_type": msg.message_type,
                    "created_at": msg.created_at.isoformat(),
                    "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                    "read_at": msg.read_at.isoformat() if msg.read_at else None,
                }
                for msg in messages
            ],
            "count": len(messages),
        }
    ), HTTPStatus.OK


@messages_bp.get("/sent")
@jwt_required()
def get_sent_messages():
    """Retrieve sent messages for current user."""
    current_user_id = get_jwt_identity()
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    messages = (
        Message.query.filter_by(sender_id=current_user_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify(
        {
            "messages": [
                {
                    "id": msg.id,
                    "recipient_id": msg.recipient_id,
                    "recipient_username": msg.recipient.username,
                    "ciphertext": msg.ciphertext,
                    "nonce": msg.nonce,
                    "message_type": msg.message_type,
                    "created_at": msg.created_at.isoformat(),
                    "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                }
                for msg in messages
            ],
            "count": len(messages),
        }
    ), HTTPStatus.OK


@messages_bp.post("/<int:message_id>/delivered")
@jwt_required()
def mark_delivered(message_id: int):
    """Mark a message as delivered."""
    current_user_id = get_jwt_identity()
    message = Message.query.filter_by(id=message_id, recipient_id=current_user_id).first()

    if not message:
        return jsonify({"error": "message not found"}), HTTPStatus.NOT_FOUND

    if not message.delivered_at:
        message.delivered_at = datetime.now(timezone.utc)
        db.session.commit()

    return jsonify({"message": "marked as delivered"}), HTTPStatus.OK


@messages_bp.post("/<int:message_id>/read")
@jwt_required()
def mark_read(message_id: int):
    """Mark a message as read."""
    current_user_id = get_jwt_identity()
    message = Message.query.filter_by(id=message_id, recipient_id=current_user_id).first()

    if not message:
        return jsonify({"error": "message not found"}), HTTPStatus.NOT_FOUND

    if not message.read_at:
        message.read_at = datetime.now(timezone.utc)
        if not message.delivered_at:
            message.delivered_at = message.read_at
        db.session.commit()

    return jsonify({"message": "marked as read"}), HTTPStatus.OK

