# VibeChat API Documentation

## Base URL
- Development: `http://localhost:5000`
- Production: `https://api.vibechat.example`

## Authentication

All protected endpoints require a JWT access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "alice",
  "password": "securepassword123",
  "display_name": "Alice" // optional
}
```

**Response:**
```json
{
  "message": "user registered successfully",
  "user_id": 1,
  "username": "alice",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "alice",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "message": "login successful",
  "user_id": 1,
  "username": "alice",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Refresh Token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Public Key Management

### Upload Public Key
```http
POST /api/keys/upload
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
  "algorithm": "Ed25519"
}
```

**Response:**
```json
{
  "message": "public key uploaded",
  "fingerprint": "a1b2c3d4e5f6...",
  "algorithm": "Ed25519"
}
```

### Get Public Key by Username
```http
GET /api/keys/bob
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "username": "bob",
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
  "fingerprint": "a1b2c3d4e5f6...",
  "algorithm": "Ed25519",
  "created_at": "2025-11-25T12:00:00Z"
}
```

## Messaging

### Send Encrypted Message
```http
POST /api/messages/send
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "recipient": "bob",
  "ciphertext": "base64-encoded-encrypted-message",
  "nonce": "base64-encoded-nonce", // optional
  "message_type": "text" // text, attachment, etc.
}
```

**Response:**
```json
{
  "message": "message sent",
  "message_id": 123,
  "created_at": "2025-11-25T12:00:00Z"
}
```

### Get Inbox
```http
GET /api/messages/inbox?limit=50&offset=0
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "messages": [
    {
      "id": 123,
      "sender_id": 1,
      "sender_username": "alice",
      "ciphertext": "base64-encoded-encrypted-message",
      "nonce": "base64-encoded-nonce",
      "message_type": "text",
      "created_at": "2025-11-25T12:00:00Z",
      "delivered_at": null,
      "read_at": null
    }
  ],
  "count": 1
}
```

### Get Sent Messages
```http
GET /api/messages/sent?limit=50&offset=0
Authorization: Bearer <access_token>
```

## WebSocket API

### Connection
```javascript
const socket = io('http://localhost:5000', {
  auth: {
    token: 'your-access-token'
  }
});
```

### Events

**Client → Server:**
- `connect` - Authenticate and join user room
- `join_room` - Join additional room (e.g., group chats)
- `leave_room` - Leave a room

**Server → Client:**
- `connected` - Connection confirmed
- `new_message` - New message received
  ```json
  {
    "message_id": 123,
    "sender_id": 1,
    "recipient_id": 2,
    "ciphertext": "base64-encoded-encrypted-message",
    "nonce": "base64-encoded-nonce",
    "message_type": "text",
    "created_at": "2025-11-25T12:00:00Z"
  }
  ```

## Error Responses

All errors follow this format:
```json
{
  "error": "error message"
}
```

**Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `409` - Conflict (e.g., username taken)
- `429` - Too Many Requests (rate limited)

