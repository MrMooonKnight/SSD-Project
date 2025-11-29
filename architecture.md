# VibeChat Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Technology Stack](#technology-stack)
4. [System Components](#system-components)
5. [Data Flow](#data-flow)
6. [Security Architecture](#security-architecture)
7. [Database Schema](#database-schema)
8. [API Design](#api-design)
9. [Real-Time Communication](#real-time-communication)
10. [Deployment Architecture](#deployment-architecture)

## System Overview

VibeChat is a secure, end-to-end encrypted web-based chat application that implements a zero-knowledge architecture. The system ensures that the server never has access to plaintext messages, providing users with verifiable confidentiality, integrity, and availability guarantees.

### Core Principles
- **Zero-Knowledge Architecture**: Server only handles encrypted ciphertext, never plaintext
- **Client-Side Cryptography**: All encryption/decryption happens in the browser using Web Crypto API
- **Minimal Backend**: Server acts as a "dumb relay" for authentication, key distribution, and message transport
- **End-to-End Encryption**: Messages are encrypted using ECDH key exchange and AES-GCM encryption

## Architecture Patterns

### Application Factory Pattern
The application uses Flask's application factory pattern (`create_app()`) for:
- Flexible configuration management
- Easy testing with different configurations
- Extension initialization in proper order
- Blueprint registration

### Blueprint Pattern
API endpoints are organized into blueprints:
- `auth_bp`: Authentication and authorization
- `keys_bp`: Public key management
- `messages_bp`: Message relay operations
- `contacts_bp`: Contact management
- `frontend_bp`: Frontend route handlers
- `health_bp`: Health check endpoints

### Repository Pattern (Implicit)
Database operations are abstracted through SQLAlchemy ORM models, providing a clean separation between business logic and data access.

## Technology Stack

### Backend
- **Framework**: Flask 3.0.3
- **Database ORM**: SQLAlchemy 3.1.1
- **Real-Time**: Flask-SocketIO 5.3.6 (WebSocket support)
- **Authentication**: Flask-JWT-Extended 4.6.0
- **Security**: Flask-CORS 4.0.1, Flask-Limiter 3.5.1
- **Configuration**: Dynaconf 3.2.4
- **Password Hashing**: Passlib with bcrypt
- **Database**: SQLite (development), PostgreSQL (production-ready)

### Frontend
- **Framework**: Vanilla JavaScript (no framework dependencies)
- **Cryptography**: Web Crypto API (SubtleCrypto)
- **Real-Time**: Socket.IO client
- **Styling**: Custom CSS
- **Templating**: Jinja2 (server-side)

### Development Tools
- **Testing**: Pytest 8.2.2
- **Linting**: Ruff 0.6.9
- **Formatting**: Black 24.8.0
- **Security Scanning**: Bandit 1.7.9
- **WSGI Server**: Gunicorn 23.0.0

## System Components

### 1. Backend Application (`backend/app/`)

#### Application Factory (`__init__.py`)
- Creates and configures Flask application instance
- Initializes all extensions (DB, JWT, CORS, SocketIO, Limiter)
- Registers blueprints
- Sets up security headers
- Creates database tables on startup

#### Configuration (`config.py`)
- Environment-based configuration using Dynaconf
- Supports multiple environments: development, testing, production
- Manages secrets, database URLs, CORS origins
- JWT configuration (token expiration, algorithm)

#### Extensions (`extensions.py`)
- Centralized extension instances:
  - `db`: SQLAlchemy database instance
  - `jwt`: JWT manager for token handling
  - `cors`: CORS configuration
  - `limiter`: Rate limiting
  - `socketio`: WebSocket server

#### Models (`models.py`)
- **User**: User accounts with email, password hash, display name
- **PublicKey**: ECDH public keys with fingerprints
- **Message**: Encrypted message storage (ciphertext, nonce, salt)
- **Contact**: User contact relationships

#### Routes (`routes/`)
- **auth.py**: Registration, login, token refresh, user info
- **keys.py**: Public key upload, retrieval by email/username
- **messages.py**: Send messages, get inbox/sent, mark delivered/read
- **contacts.py**: Add, list, remove contacts
- **frontend.py**: Serve HTML templates
- **health.py**: Health check endpoints

#### WebSocket Handlers (`socketio_handlers.py`)
- Connection authentication via JWT
- User-specific room management
- Real-time message delivery
- Connection/disconnection handling

#### Security (`security/headers.py`)
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options, X-Content-Type-Options
- Referrer-Policy, Permissions-Policy

### 2. Frontend Application (`backend/app/static/`)

#### JavaScript Modules

**crypto.js** - Web Crypto API Wrapper
- `CryptoManager` class for encryption operations
- Key pair generation (ECDH P-256)
- Public key export/import (SPKI format)
- Shared secret derivation
- Message encryption/decryption (AES-GCM)
- PBKDF2 key derivation

**chat.js** - Chat Application Logic
- User authentication and session management
- Contact management
- Message sending and receiving
- Real-time WebSocket communication
- UI event handling
- Message rendering and display

#### Templates (`templates/`)
- **base.html**: Base template with common layout
- **index.html**: Landing page
- **login.html**: Login form
- **register.html**: Registration form
- **chat.html**: Main chat interface

#### Styling (`static/css/style.css`)
- Responsive layout
- Chat message bubbles (sent/received)
- Contact list styling
- Modal dialogs
- Form styling

## Data Flow

### 1. User Registration Flow
```
User → Register Form → POST /api/auth/register
  → Server validates email/password
  → Password hashed with bcrypt
  → User record created in database
  → JWT tokens generated
  → Redirect to chat interface
```

### 2. Key Generation and Upload Flow
```
User Login → Browser generates ECDH key pair
  → Private key stays in browser memory
  → Public key exported as base64 SPKI
  → POST /api/keys/upload
  → Server validates and stores public key
  → Key fingerprint computed (SHA-256)
```

### 3. Message Sending Flow
```
User types message → Click Send
  → Fetch recipient's public key (GET /api/keys/email/<email>)
  → Derive shared secret using ECDH
  → Derive AES-GCM key using PBKDF2
  → Encrypt message with AES-GCM
  → POST /api/messages/send (ciphertext, nonce, salt)
  → Server stores encrypted message
  → WebSocket emits to recipient
  → Recipient receives and decrypts
```

### 4. Message Receiving Flow
```
WebSocket receives new_message event
  → Load messages (GET /api/messages/inbox)
  → For each message:
    → Fetch sender's public key
    → Derive shared secret using ECDH
    → Derive AES-GCM key using PBKDF2 with stored salt
    → Decrypt message with AES-GCM
    → Display in chat interface
```

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: Access tokens (short-lived) and refresh tokens (long-lived)
- **Token Storage**: Browser localStorage (consider httpOnly cookies for production)
- **Token Validation**: All protected endpoints validate JWT signature
- **Password Security**: bcrypt hashing with appropriate cost factor

### Encryption
- **Key Exchange**: ECDH (Elliptic Curve Diffie-Hellman) with P-256 curve
- **Symmetric Encryption**: AES-GCM 256-bit
- **Key Derivation**: PBKDF2 with SHA-256, 100,000 iterations
- **Nonce/IV**: Unique per message, sent with ciphertext
- **Salt**: Unique per message for key derivation

### Transport Security
- **HTTPS**: Required in production (configured for development)
- **WebSocket**: Secure WebSocket (WSS) in production
- **CORS**: Configurable origins, credentials support
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.

### Rate Limiting
- Flask-Limiter configured on API endpoints
- Prevents brute force attacks
- Configurable per endpoint

### Input Validation
- Server-side validation of all inputs
- Email format validation
- Public key format validation
- SQL injection prevention via SQLAlchemy ORM

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

### PublicKeys Table
```sql
CREATE TABLE public_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    public_key_pem TEXT NOT NULL,
    fingerprint VARCHAR(64) NOT NULL,
    algorithm VARCHAR(20) NOT NULL DEFAULT 'ECDH',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(id),
    recipient_id INTEGER NOT NULL REFERENCES users(id),
    ciphertext TEXT NOT NULL,
    nonce VARCHAR(64),
    salt VARCHAR(64),
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    created_at TIMESTAMP NOT NULL,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP
);
```

### Contacts Table
```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    contact_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL,
    UNIQUE(user_id, contact_id)
);
```

## API Design

### RESTful Endpoints

#### Authentication (`/api/auth`)
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Authenticate and receive JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current authenticated user info

#### Public Keys (`/api/keys`)
- `POST /api/keys/upload` - Upload or update user's public key
- `GET /api/keys/email/<email>` - Get public key by user email
- `GET /api/keys/me` - Get current user's public key

#### Messages (`/api/messages`)
- `POST /api/messages/send` - Send encrypted message to recipient
- `GET /api/messages/inbox` - Get received messages (paginated)
- `GET /api/messages/sent` - Get sent messages (paginated)
- `DELETE /api/messages/conversation/<email>` - Clear conversation with user
- `POST /api/messages/<id>/delivered` - Mark message as delivered
- `POST /api/messages/<id>/read` - Mark message as read

#### Contacts (`/api/contacts`)
- `POST /api/contacts/add` - Add contact by email
- `GET /api/contacts/list` - Get all contacts
- `DELETE /api/contacts/<id>` - Remove contact

#### Health (`/api/health`)
- `GET /api/health/live` - Liveness probe
- `GET /api/health/ready` - Readiness probe

### WebSocket Events

#### Client → Server
- `connect` - Authenticate and establish connection (requires JWT in auth)

#### Server → Client
- `connected` - Connection confirmed with user info
- `new_message` - Real-time message delivery notification
- `disconnect` - Connection terminated

## Real-Time Communication

### WebSocket Architecture
- **Library**: Flask-SocketIO with Socket.IO protocol
- **Transport**: WebSocket with polling fallback
- **Authentication**: JWT token in connection auth
- **Rooms**: User-specific rooms (`user_{user_id}`) for targeted delivery
- **Message Broadcasting**: Server emits to recipient's room only

### Connection Flow
```
Client → WebSocket connect with JWT
  → Server validates JWT
  → Server joins user to room: user_{user_id}
  → Server emits 'connected' event
  → Client ready to receive messages
```

### Message Delivery Flow
```
Sender sends message → POST /api/messages/send
  → Server stores message in database
  → Server emits 'new_message' to recipient's room
  → Recipient's WebSocket receives event
  → Client reloads messages
  → Message appears in chat interface
```

## Deployment Architecture

### Development
- Flask development server (`run.py`)
- SQLite database
- Single process, single thread
- Debug mode enabled

### Production (Recommended)
- **WSGI Server**: Gunicorn with multiple workers
- **Database**: PostgreSQL with connection pooling
- **Reverse Proxy**: Nginx for static files and SSL termination
- **Process Manager**: systemd or supervisor
- **SSL/TLS**: Let's Encrypt certificates
- **Monitoring**: Application logs, health checks

### Environment Configuration
- Development: `settings.toml` or environment variables
- Production: Environment variables or secure config management
- Secrets: Never committed to repository, use secure vault

## Security Considerations

### Client-Side Security
- Private keys never leave browser memory
- No plaintext message storage in browser
- XSS protection via CSP headers
- Input sanitization

### Server-Side Security
- SQL injection prevention (ORM)
- XSS prevention (template escaping)
- CSRF protection (same-origin policy)
- Rate limiting on sensitive endpoints
- Security headers enforcement

### Cryptographic Security
- Strong key derivation (PBKDF2 with 100k iterations)
- Unique nonces per message
- Authenticated encryption (AES-GCM)
- Secure key exchange (ECDH)

## Scalability Considerations

### Current Limitations
- Single server deployment
- SQLite for development (not suitable for production scale)
- In-memory WebSocket connections

### Future Improvements
- Database connection pooling
- Redis for WebSocket session management
- Message queue for offline delivery
- Horizontal scaling with load balancer
- CDN for static assets

## Monitoring and Logging

### Logging
- Application logs via Flask's logging
- Error tracking and debugging
- Security event logging

### Health Checks
- Liveness probe: Basic application health
- Readiness probe: Database connectivity, dependencies

## Testing Strategy

### Unit Tests
- Model validation
- Cryptographic operations
- API endpoint logic

### Integration Tests
- End-to-end message flow
- Authentication flow
- WebSocket communication

### Security Tests
- Bandit static analysis
- Dependency vulnerability scanning
- Manual penetration testing

