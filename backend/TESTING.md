# Testing Guide for VibeChat API

## Quick Start

### 1. Start the Server

```powershell
cd backend
python run.py
```

The server will start on `http://localhost:5000`

### 2. Test with Python Script

```powershell
# In a new terminal
cd backend
python test_api.py
```

This script will:
- Register two test users (Alice and Bob)
- Test authentication
- Upload public keys
- Send encrypted messages
- Retrieve messages

## Manual Testing with cURL

### 1. Register a User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123",
    "display_name": "Alice"
  }'
```

**Expected Response:**
```json
{
  "message": "user registered successfully",
  "user_id": 1,
  "username": "alice",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "password123"
  }'
```

### 3. Get Current User Info

```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Upload Public Key

```bash
curl -X POST http://localhost:5000/api/keys/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
    "algorithm": "Ed25519"
  }'
```

### 5. Get Public Key by Username

```bash
curl -X GET http://localhost:5000/api/keys/bob \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Send Encrypted Message

```bash
curl -X POST http://localhost:5000/api/messages/send \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "bob",
    "ciphertext": "dGVzdC1lbmNyeXB0ZWQtbWVzc2FnZQ==",
    "nonce": "nonce123",
    "message_type": "text"
  }'
```

### 7. Get Inbox

```bash
curl -X GET "http://localhost:5000/api/messages/inbox?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 8. Get Sent Messages

```bash
curl -X GET "http://localhost:5000/api/messages/sent?limit=50&offset=0" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Testing with Postman

### Import Collection

1. Open Postman
2. Create a new collection called "VibeChat API"
3. Set collection variable: `base_url` = `http://localhost:5000/api`
4. Set collection variable: `access_token` = (will be set automatically)

### Request Examples

#### Register User
- **Method:** POST
- **URL:** `{{base_url}}/auth/register`
- **Body (JSON):**
```json
{
  "username": "alice",
  "password": "password123",
  "display_name": "Alice"
}
```
- **Tests Tab (to save token):**
```javascript
if (pm.response.code === 201) {
    const jsonData = pm.response.json();
    pm.collectionVariables.set("access_token", jsonData.access_token);
}
```

#### Login
- **Method:** POST
- **URL:** `{{base_url}}/auth/login`
- **Body (JSON):**
```json
{
  "username": "alice",
  "password": "password123"
}
```

#### Get Current User
- **Method:** GET
- **URL:** `{{base_url}}/auth/me`
- **Headers:**
  - `Authorization: Bearer {{access_token}}`

#### Upload Public Key
- **Method:** POST
- **URL:** `{{base_url}}/keys/upload`
- **Headers:**
  - `Authorization: Bearer {{access_token}}`
  - `Content-Type: application/json`
- **Body (JSON):**
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
  "algorithm": "Ed25519"
}
```

#### Send Message
- **Method:** POST
- **URL:** `{{base_url}}/messages/send`
- **Headers:**
  - `Authorization: Bearer {{access_token}}`
  - `Content-Type: application/json`
- **Body (JSON):**
```json
{
  "recipient": "bob",
  "ciphertext": "base64-encoded-encrypted-message",
  "nonce": "optional-nonce",
  "message_type": "text"
}
```

## Testing WebSocket Connection

### Using Python

```python
import socketio
import time

# Create client
sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.event
def connected(data):
    print(f'Connection confirmed: {data}')

@sio.event
def new_message(data):
    print(f'New message received: {data}')

@sio.event
def disconnect():
    print('Disconnected from server')

# Connect with JWT token
sio.connect(
    'http://localhost:5000',
    auth={'token': 'YOUR_ACCESS_TOKEN'}
)

# Keep connection alive
time.sleep(10)
sio.disconnect()
```

### Using JavaScript (Browser Console)

```javascript
const socket = io('http://localhost:5000', {
  auth: {
    token: 'YOUR_ACCESS_TOKEN'
  }
});

socket.on('connect', () => {
  console.log('Connected');
});

socket.on('connected', (data) => {
  console.log('Connection confirmed:', data);
});

socket.on('new_message', (data) => {
  console.log('New message:', data);
});

socket.on('disconnect', () => {
  console.log('Disconnected');
});
```

## Testing Health Endpoints

### Liveness Check
```bash
curl http://localhost:5000/api/health/live
```

### Readiness Check
```bash
curl http://localhost:5000/api/health/ready
```

## Common Issues

### Connection Refused
- Make sure the server is running on port 5000
- Check if another process is using port 5000

### 401 Unauthorized
- Verify your access token is valid
- Check if token has expired (default: 1 hour)
- Use `/api/auth/refresh` to get a new token

### 404 Not Found
- Verify the endpoint URL is correct
- Check if the server is running the latest code

### Database Errors
- Delete `backend/instance/vibechat.db` and restart server
- The database will be recreated automatically

## Automated Testing

Run the test suite:
```powershell
.\.venv\Scripts\python -m pytest backend\tests -v
```

Run with coverage:
```powershell
.\.venv\Scripts\python -m pytest backend\tests --cov=backend/app --cov-report=html
```

