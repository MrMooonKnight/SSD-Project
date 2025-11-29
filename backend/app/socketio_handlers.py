"""WebSocket event handlers for real-time messaging."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import disconnect, emit, join_room, leave_room

from .extensions import socketio
from .models import User


@socketio.on("connect")
def handle_connect(auth: dict | None = None):
    """Handle WebSocket connection with JWT authentication."""
    if not auth or "token" not in auth:
        disconnect()
        return False

    try:
        token = auth["token"]
        decoded = decode_token(token)
        user_id = decoded.get("sub")
        if not user_id:
            disconnect()
            return False

        # Verify user exists and is active
        from .extensions import db

        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            disconnect()
            return False

        # Join user-specific room for message delivery
        join_room(f"user_{user_id}")
        emit("connected", {"user_id": user_id, "username": user.username})
        return True
    except Exception:
        disconnect()
        return False


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    # Room cleanup is automatic
    pass


@socketio.on("join_room")
def handle_join_room(data: dict):
    """Allow joining additional rooms (e.g., group chats)."""
    room = data.get("room")
    if room:
        join_room(room)
        emit("joined_room", {"room": room})


@socketio.on("leave_room")
def handle_leave_room(data: dict):
    """Leave a room."""
    room = data.get("room")
    if room:
        leave_room(room)
        emit("left_room", {"room": room})

