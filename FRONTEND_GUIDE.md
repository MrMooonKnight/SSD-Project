# VibeChat Frontend Guide

## Overview

The frontend is now fully implemented as a Flask-based web application with:
- Email-based authentication (registration/login)
- Contact management (add contacts by email)
- End-to-end encrypted chat using Web Crypto API
- Real-time messaging via WebSocket

## Features

### 1. Authentication
- **Registration**: Create account with email and password
- **Login**: Authenticate with email and password
- **JWT Tokens**: Secure session management

### 2. Contact Management
- **Add Contacts**: Add other users by their email address
- **Contact List**: View all your contacts
- **Remove Contacts**: Delete contacts from your list

### 3. Encrypted Chat
- **End-to-End Encryption**: Messages encrypted using Web Crypto API (ECDH + AES-GCM)
- **Key Exchange**: Public keys automatically exchanged when adding contacts
- **Real-Time Delivery**: WebSocket for instant message delivery
- **Message History**: View conversation history with any contact

## How to Use

### Starting the Application

1. **Start the Flask server:**
   ```powershell
   cd backend
   python run.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5000`

### Testing with Two Users

1. **Register First User:**
   - Go to `http://localhost:5000/register`
   - Enter email: `alice@example.com`
   - Enter password: `password123`
   - Click "Register"
   - You'll be automatically logged in and redirected to chat

2. **Register Second User (in incognito/private window or different browser):**
   - Go to `http://localhost:5000/register`
   - Enter email: `bob@example.com`
   - Enter password: `password456`
   - Click "Register"

3. **Add Contact:**
   - In Alice's browser, click "+ Add" in the contacts section
   - Enter Bob's email: `bob@example.com`
   - Click "Add Contact"
   - Bob should now appear in Alice's contact list

4. **Start Chatting:**
   - Click on Bob's name in the contact list
   - Type a message and click "Send"
   - The message will be encrypted and sent to Bob
   - In Bob's browser, add Alice as a contact
   - Bob can then see and decrypt Alice's messages
   - Bob can reply, and Alice will see the encrypted reply

## Technical Details

### Encryption Flow

1. **Key Generation:**
   - On first login, browser generates ECDH key pair (P-256 curve)
   - Public key is uploaded to server
   - Private key stays in browser memory (not stored)

2. **Message Encryption:**
   - When sending a message:
     - Fetch recipient's public key from server
     - Derive shared secret using ECDH
     - Derive AES-GCM key using PBKDF2
     - Encrypt message with AES-GCM
     - Send ciphertext, nonce, and salt to server

3. **Message Decryption:**
   - When receiving a message:
     - Use sender's public key (from contact)
     - Derive shared secret using ECDH
     - Derive AES-GCM key using PBKDF2 with stored salt
     - Decrypt message with AES-GCM

### Security Features

- **Zero-Knowledge Architecture**: Server never sees plaintext messages
- **End-to-End Encryption**: Only sender and recipient can decrypt
- **Secure Key Exchange**: Public keys verified through server
- **JWT Authentication**: Secure session management
- **HTTPS Ready**: Configured for secure transport

## File Structure

```
backend/
├── app/
│   ├── templates/          # HTML templates
│   │   ├── base.html       # Base template
│   │   ├── index.html      # Home page
│   │   ├── login.html      # Login page
│   │   ├── register.html   # Registration page
│   │   └── chat.html       # Chat interface
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css   # Styling
│   │   └── js/
│   │       ├── crypto.js   # Web Crypto API wrapper
│   │       └── chat.js     # Chat application logic
│   └── routes/
│       └── frontend.py     # Frontend route handlers
```

## API Endpoints Used by Frontend

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `POST /api/contacts/add` - Add contact
- `GET /api/contacts/list` - List contacts
- `POST /api/keys/upload` - Upload public key
- `GET /api/keys/email/<email>` - Get public key by email
- `POST /api/messages/send` - Send message
- `GET /api/messages/inbox` - Get received messages
- `GET /api/messages/sent` - Get sent messages

## WebSocket Events

- `connect` - Connect with JWT token
- `new_message` - Receive new message notification
- `disconnect` - Handle disconnection

## Troubleshooting

### Messages not decrypting
- Ensure both users have added each other as contacts
- Check browser console for errors
- Verify public keys are uploaded (check Network tab)

### WebSocket not connecting
- Check browser console for connection errors
- Verify JWT token is valid
- Ensure server is running with SocketIO support

### Contact not found
- Verify the email is registered
- Check spelling of email address
- Ensure user account is active

## Next Steps

For production deployment:
1. Enable HTTPS
2. Store private keys encrypted with user password
3. Implement key rotation
4. Add message persistence in IndexedDB
5. Add file attachment support
6. Implement group messaging

