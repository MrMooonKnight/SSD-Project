"""Message endpoints for room-based chat (no authentication required)."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, jsonify, request

from ..extensions import db, socketio
from ..models import ChatRoom, RoomMessage

messages_bp = Blueprint("messages", __name__)


@messages_bp.post("/rooms/<room_slug>/messages")
def send_message(room_slug: str):
    """Send a message to a chat room."""
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    content = payload.get("content", "").strip()

    if not username:
        return jsonify({"error": "username required"}), HTTPStatus.BAD_REQUEST

    if not content:
        return jsonify({"error": "content required"}), HTTPStatus.BAD_REQUEST

    if len(username) > 100:
        return jsonify({"error": "username too long (max 100 characters)"}), HTTPStatus.BAD_REQUEST

    if len(content) > 10000:
        return jsonify({"error": "message too long (max 10000 characters)"}), HTTPStatus.BAD_REQUEST

    # Get or create room
    room = ChatRoom.query.filter_by(room_slug=room_slug).first()
    if not room:
        room = ChatRoom(room_slug=room_slug)
        db.session.add(room)
        db.session.flush()  # Get room.id

    # Create message
    message = RoomMessage(
        room_id=room.id,
        username=username,
        content=content,
    )
    db.session.add(message)
    
    # Update room's last_message_at
    room.last_message_at = message.created_at
    
    db.session.commit()

    # Emit via WebSocket for real-time delivery
    socketio.emit(
        "new_message",
        {
            "message_id": message.id,
            "room_slug": room_slug,
            "username": username,
            "content": content,
            "created_at": message.created_at.isoformat(),
        },
        room=f"room_{room_slug}",
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


@messages_bp.get("/rooms/<room_slug>/messages")
def get_messages(room_slug: str):
    """Retrieve messages for a chat room."""
    room = ChatRoom.query.filter_by(room_slug=room_slug).first()
    if not room:
        # Return empty list if room doesn't exist
        return jsonify({"messages": [], "count": 0}), HTTPStatus.OK

    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    messages = (
        RoomMessage.query.filter_by(room_id=room.id)
        .order_by(RoomMessage.created_at.asc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return jsonify(
        {
            "messages": [
                {
                    "id": msg.id,
                    "username": msg.username,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
            "count": len(messages),
        }
    ), HTTPStatus.OK


@messages_bp.delete("/rooms/<room_slug>/messages")
def clear_messages(room_slug: str):
    """Delete all messages in a chat room."""
    room = ChatRoom.query.filter_by(room_slug=room_slug).first()
    if not room:
        return jsonify({"error": "room not found"}), HTTPStatus.NOT_FOUND

    deleted = RoomMessage.query.filter_by(room_id=room.id).delete(synchronize_session=False)
    room.last_message_at = None
    db.session.commit()

    # Notify all clients in the room
    socketio.emit("messages_cleared", {"room_slug": room_slug}, room=f"room_{room_slug}")

    return jsonify({"message": f"Deleted {deleted} messages"}), HTTPStatus.OK
