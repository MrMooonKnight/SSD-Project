"""WebSocket event handlers for real-time messaging in chat rooms."""

from __future__ import annotations

from flask_socketio import emit, join_room, leave_room

from .extensions import socketio

# Track active users per room: {room_slug: {username: set of session_ids}}
room_users: dict[str, dict[str, set]] = {}


@socketio.on("connect")
def handle_connect():
    """Handle WebSocket connection - no authentication required."""
    emit("connected", {"status": "connected"})
    return True


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection."""
    from flask import request
    
    # Find and remove user from all rooms
    session_id = request.sid
    rooms_to_update = []
    
    for room_slug, users_dict in room_users.items():
        for username, session_ids in list(users_dict.items()):
            if session_id in session_ids:
                session_ids.discard(session_id)
                if not session_ids:  # No more sessions for this user
                    del users_dict[username]
                    rooms_to_update.append((room_slug, username))
    
    # Notify rooms of user leaving
    for room_slug, username in rooms_to_update:
        room_name = f"room_{room_slug}"
        emit("user_left", {"room_slug": room_slug, "username": username}, room=room_name)


@socketio.on("join_room")
def handle_join_room(data: dict):
    """Join a chat room."""
    from flask import request
    
    room_slug = data.get("room_slug")
    username = data.get("username")
    session_id = request.sid
    
    if room_slug:
        room_name = f"room_{room_slug}"
        join_room(room_name)
        
        # Track user in room
        if room_slug not in room_users:
            room_users[room_slug] = {}
        if username not in room_users[room_slug]:
            room_users[room_slug][username] = set()
        room_users[room_slug][username].add(session_id)
        
        emit("joined_room", {"room_slug": room_slug})
        
        # Notify others in room
        if username:
            emit("user_joined", {"room_slug": room_slug, "username": username}, room=room_name, include_self=False)
            
            # Send current active users to the new user
            active_users = list(room_users[room_slug].keys())
            emit("active_users", {"room_slug": room_slug, "users": active_users})


@socketio.on("user_joined")
def handle_user_joined(data: dict):
    """Handle explicit user join notification."""
    from flask import request
    
    room_slug = data.get("room_slug")
    username = data.get("username")
    session_id = request.sid
    
    if room_slug and username:
        room_name = f"room_{room_slug}"
        
        # Track user in room
        if room_slug not in room_users:
            room_users[room_slug] = {}
        if username not in room_users[room_slug]:
            room_users[room_slug][username] = set()
        room_users[room_slug][username].add(session_id)
        
        # Notify others in room
        emit("user_joined", {"room_slug": room_slug, "username": username}, room=room_name, include_self=False)


@socketio.on("user_left")
def handle_user_left(data: dict):
    """Handle explicit user leave notification."""
    from flask import request
    
    room_slug = data.get("room_slug")
    username = data.get("username")
    session_id = request.sid
    
    if room_slug and username:
        room_name = f"room_{room_slug}"
        
        # Remove user from room tracking
        if room_slug in room_users and username in room_users[room_slug]:
            room_users[room_slug][username].discard(session_id)
            if not room_users[room_slug][username]:  # No more sessions for this user
                del room_users[room_slug][username]
        
        # Notify others in room
        emit("user_left", {"room_slug": room_slug, "username": username}, room=room_name, include_self=False)


@socketio.on("leave_room")
def handle_leave_room(data: dict):
    """Leave a chat room."""
    from flask import request
    
    room_slug = data.get("room_slug")
    username = data.get("username")
    session_id = request.sid
    
    if room_slug:
        room_name = f"room_{room_slug}"
        leave_room(room_name)
        
        # Remove user from room tracking
        if room_slug in room_users and username and username in room_users[room_slug]:
            room_users[room_slug][username].discard(session_id)
            if not room_users[room_slug][username]:  # No more sessions for this user
                del room_users[room_slug][username]
                # Notify others in room
                emit("user_left", {"room_slug": room_slug, "username": username}, room=room_name)
        
        emit("left_room", {"room_slug": room_slug})
