# Secure & Encrypted Web-Based Chat Application
Secure Software Design project proposal for FAST-NUCES, Fall 2025.

## Implementation Overview

VibeChat is a fully functional secure chat application with end-to-end encryption. The system implements a zero-knowledge architecture where the server never has access to plaintext messages.

### Project Structure

```
SSD-Project/
├── backend/
│   ├── app/                    # Main application package
│   │   ├── __init__.py         # Application factory
│   │   ├── config.py           # Configuration management (Dynaconf)
│   │   ├── extensions.py       # Flask extensions initialization
│   │   ├── models.py           # SQLAlchemy database models
│   │   ├── routes/             # API route blueprints
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── contacts.py     # Contact management
│   │   │   ├── frontend.py     # Frontend route handlers
│   │   │   ├── health.py       # Health check endpoints
│   │   │   ├── keys.py         # Public key management
│   │   │   └── messages.py     # Message relay endpoints
│   │   ├── security/
│   │   │   └── headers.py      # Security headers configuration
│   │   ├── socketio_handlers.py # WebSocket event handlers
│   │   ├── static/             # Frontend assets
│   │   │   ├── css/
│   │   │   │   └── style.css   # Application styles
│   │   │   └── js/
│   │   │       ├── crypto.js   # Web Crypto API wrapper
│   │   │       └── chat.js     # Chat application logic
│   │   └── templates/          # Jinja2 HTML templates
│   │       ├── base.html
│   │       ├── chat.html
│   │       ├── login.html
│   │       └── register.html
│   ├── tests/                  # Test suite
│   ├── requirements.txt        # Python dependencies
│   ├── run.py                  # Development server
│   └── wsgi.py                 # Production WSGI entry point
├── architecture.md             # Detailed architecture documentation
└── README.md                   # This file
```

### API Endpoints

#### Authentication (`/api/auth`)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Authenticate and get JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

#### Public Keys (`/api/keys`)
- `POST /api/keys/upload` - Upload/update user's public key
- `GET /api/keys/email/<email>` - Get public key by user email
- `GET /api/keys/me` - Get current user's public key

#### Messages (`/api/messages`)
- `POST /api/messages/send` - Send encrypted message
- `GET /api/messages/inbox` - Get received messages (paginated)
- `GET /api/messages/sent` - Get sent messages (paginated)
- `DELETE /api/messages/conversation/<email>` - Clear conversation with user
- `POST /api/messages/<id>/delivered` - Mark message as delivered
- `POST /api/messages/<id>/read` - Mark message as read

#### Contacts (`/api/contacts`)
- `POST /api/contacts/add` - Add contact by email
- `GET /api/contacts/list` - Get all contacts
- `DELETE /api/contacts/<id>` - Remove contact

#### WebSocket Events
- `connect` - Authenticate and join user room
- `new_message` - Real-time message delivery
- `disconnect` - Cleanup on disconnect

## Quick Start

### Prerequisites
- Python 3.12 or higher
- pip package manager

### Local Development (Windows/PowerShell)

```powershell
# Navigate to project directory
cd SSD-Project

# Setup virtual environment
python -m venv backend\venv
backend\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend\requirements.txt

# Set environment variables (optional, defaults provided)
$env:VIBE_SECRET_KEY = "your-secret-key-here"
$env:VIBE_JWT_SECRET_KEY = "your-jwt-secret-here"

# Run development server
cd backend
python run.py
```

The server will start on `http://localhost:5000` with WebSocket support.

### Using the Application

1. **Register a new account**: Navigate to `http://localhost:5000/register`
2. **Login**: Use your credentials at `http://localhost:5000/login`
3. **Add contacts**: Click "+ Add" in the contacts section and enter a user's email
4. **Start chatting**: Select a contact and send encrypted messages

### Testing with Multiple Users

1. Open the application in two different browsers (or incognito windows)
2. Register two different accounts
3. Add each other as contacts
4. Start sending messages - they will be encrypted end-to-end

### Run Tests & Static Analysis

```powershell
# Activate virtual environment
backend\venv\Scripts\Activate.ps1

# Run tests
pytest backend\tests -v

# Security linting
bandit -r backend

# Code formatting check
ruff check backend
black --check backend
```

## Features

### Security Features
- **End-to-End Encryption**: Messages encrypted using ECDH key exchange and AES-GCM
- **Zero-Knowledge Architecture**: Server never sees plaintext messages
- **Secure Key Management**: Public keys stored with SHA-256 fingerprints
- **JWT Authentication**: Secure session management with access and refresh tokens
- **Security Headers**: CSP, HSTS, X-Frame-Options, and more

### Application Features
- **User Registration & Login**: Secure account creation and authentication
- **Contact Management**: Add and manage contacts by email
- **Real-Time Messaging**: WebSocket-based instant message delivery
- **Message History**: View conversation history with any contact
- **Clear Conversations**: Delete all messages in a conversation

## Architecture

For detailed architecture documentation, see [architecture.md](architecture.md).

### Key Components
- **Backend**: Flask application with SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript with Web Crypto API
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **Real-Time**: Flask-SocketIO for WebSocket communication
- **Encryption**: Web Crypto API (ECDH P-256, AES-GCM 256-bit)

## Documentation

- [Architecture Documentation](architecture.md) - Detailed system architecture
- [API Documentation](backend/API.md) - API endpoint reference
- [Frontend Guide](FRONTEND_GUIDE.md) - Frontend implementation details
- [Testing Guide](backend/TESTING.md) - Testing procedures

## 1. Title of the Project
- Secure & Encrypted Web-Based Chat Application (codename: VibeChat)
- Provides verifiable confidentiality, integrity, and availability guarantees for browser-based conversations
- Serves as a reference implementation for secure software design practices in academic settings

## 2. Team Information
- **Section:** CY-C, FAST School of Computing, Islamabad
- **Team Name:** Vibe Coders
- **Members:**
  - Talha Asghar — i221554
  - Uzzam Arif — i221748
  - Adeen Ilyas — i221573
  - Abdul Hanan — i221586
  - Ammar Bangash — i221626

## 3. Problem Statement
Modern web chat tools centralize message storage and cryptography, exposing users to:
- Server-side data breaches that leak unencrypted or weakly encrypted conversations.
- Man-in-the-middle (MITM) attacks where adversaries tamper with public keys, TLS certs, or session tokens during key exchange.
- Insider threats where platform operators can inspect message payloads or respond to coercive data demands.
- Regulatory and compliance gaps when confidentiality assurances cannot be proven or audited.

These risks translate into reputational damage, legal liability, and a lack of user trust. We aim to eliminate provider visibility into user content by enforcing client-side end-to-end encryption (E2EE), auditable key authenticity, and secure key custody from project inception.

## 4. Objectives of the Project
1. Ship a browser-based chat experience that enables one-to-one and group messaging with default E2EE.
2. Implement zero-knowledge key management so private keys never leave user control; introduce passphrase-based key wrapping plus recovery options.
3. Maintain a “dumb relay” backend that only handles authentication, presence, and ciphertext transport.
4. Embed mitigations for MITM, replay, CSRF, XSS, and injection vectors by combining secure headers, CSP, sanitization, and certificate pinning guidance.
5. Document the security-centric SDLC—from threat modeling through verification—demonstrating adherence to course requirements.

## 5. Proposed Solution & Architecture
### 5.1 System Overview
The solution follows a zero-trust, client-driven cryptography model with a minimal backend.

- **Client (React SPA):**
  - Generates asymmetric key pairs on registration via Web Crypto (Curve25519 / Ed25519 for ECDH + signatures).
  - Wraps private keys with Argon2id-hardened passphrases and stores them in IndexedDB; session-only keys reside in memory.
  - Uses access tokens (JWT) for session continuity; refresh logic leverages silent re-auth with short-lived tokens.
  - Fetches recipient public keys from backend, performs Diffie-Hellman to derive symmetric session keys (XChaCha20-Poly1305) per conversation, and encrypts messages plus attachments locally.
  - Displays key fingerprints (SHA-256 truncated) so users can verify identities out-of-band and detect key substitutions.
- **Server (Flask + Flask-SocketIO + SQLAlchemy):**
  - Handles registration, login, JWT token issuance, and account management workflows.
  - Persists public keys, user metadata, and encrypted message envelopes in SQLite (development) / PostgreSQL (production) with strict access controls.
  - Relays ciphertext over secure WebSockets; no plaintext is logged or inspected, aligning with least-knowledge architecture.
  - Implements rate limiting, security headers (CSP, HSTS), CORS policies, and audit logging for compliance.

### 5.2 Security Principles & Controls
- **Least Privilege:** Backend can only access metadata; privilege separation between auth API, message relay, and admin tooling enforced via service accounts and IAM.
- **Defense in Depth:** CSP, HSTS, secure cookies, strict transport security headers, subresource integrity, and automated dependency scanning keep the attack surface constrained.
- **Key Authenticity:** TOFU (trust on first use) plus manual fingerprint confirmation; future work: integrate Web of Trust, QR verification, or transparency logs.
- **Forward Secrecy:** Per-message symmetric keys derived using X25519 ratchets; compromised keys do not decrypt historical traffic because session keys are ephemeral.
- **Availability:** Multi-region Firestore plus queued delivery to tolerate offline recipients; WebSocket fallback to HTTPS long polling ensures continuity during partial outages.
- **Privacy by Design:** Metadata minimization, optional anonymous display names, and retention policies that purge delivered ciphertext after configurable windows.

### 5.3 Data Flow Summary
1. User registers → SPA generates keys → private key encrypted (passphrase + Argon2id) → stored in IndexedDB; public key uploaded with integrity checks.
2. Sender selects chat → SPA fetches recipient public key → derives shared secret → encrypts payload + metadata (nonce, attachments, signatures) → sends to backend relay.
3. Backend validates sender session, stamps metadata, applies rate limits, and relays ciphertext to recipient channel; undelivered packets reside encrypted in Firestore queues.
4. Recipient SPA decrypts using local private key; messages never touch disk in plaintext and are optionally re-encrypted for secure local backups.

## 6. Methodology (Security-centric SDLC)
1. **Requirements & Planning (Weeks 1–4)**
   - Capture functional + security requirements, define misuse cases, and establish compliance targets (e.g., OWASP ASVS L2, GDPR privacy expectations).
   - Perform STRIDE-based threat modeling with layered data flow diagrams; document mitigations, assumptions, and residual risk for instructor review.
2. **Design (Weeks 3–6)**
   - Define API contracts, database schema, key lifecycle diagrams, and crypto module boundaries.
   - Review design against NIST SP 800-64 Rev.2 and OWASP Proactive Controls; hold peer design reviews with security checklists.
3. **Implementation (Weeks 5–12)**
   - Follow secure coding guidelines, typed interfaces, eslint-plugin-security, Prettier, and Husky hooks; enforce commit signing.
   - Integrate dependency scanning (npm audit, Snyk) and secret scanning (Git hooks, GitHub Advanced Security) in CI pipelines.
4. **Verification & Validation (Weeks 9–16)**
   - Unit + integration tests with Jest/React Testing Library and supertest, focusing on crypto wrappers and transport logic.
   - Security testing: automated ZAP/Burp scans, dependency vulnerability triage, manual penetration tests focusing on authentication, WebSocket flows, and key attestation.
   - Prepare adversary emulation scenarios (e.g., MITM, replay, XSS injection) and document outcomes.
5. **Deployment & Maintenance (Weeks 15–20)**
   - Containerize services, enable CI/CD with GitHub Actions, and enforce SAST/DAST gates pre-deployment.
   - Prepare incident response playbooks, logging strategy, monitoring alerts, and key compromise recovery workflow.

## 7. Tools and Technologies
- **Frontend:** Vanilla JavaScript, Web Crypto API, Socket.IO client, Custom CSS
- **Cryptography:** Web Crypto API (SubtleCrypto) for ECDH key generation, AES-GCM encryption, PBKDF2 key derivation
- **Backend:** Python 3.12+, Flask 3.0, Flask-SocketIO, SQLAlchemy, SQLite (dev) / PostgreSQL (prod), Gunicorn for production
- **Security Tooling:** Bandit (security linting), Ruff (code linting), Black (code formatting), Pytest (testing)
- **DevOps:** Gunicorn (WSGI server), environment-based configuration with Dynaconf

## 8. Expected Deliverables
- Working SPA + backend demonstrating secure registration, login, messaging, and attachment sharing with E2EE, hosted on Firebase for evaluation.
- Technical design dossier: architecture diagrams, threat model artifacts, trust boundaries, crypto rationale, and data retention policies.
- Security test report summarizing tooling, testing scope, findings, fixes, and residual risks, including penetration test evidence.
- Final presentation + demo with threat walkthrough, lessons learned, and future roadmap (mobile clients, multi-device sync, transparency logs).

## 9. Timeline (20 Weeks)
| Weeks | Milestones |
| --- | --- |
| 1–2 | Requirement elicitation, stakeholder interviews, success metrics |
| 3–4 | Threat modeling, data flow diagrams, security requirements baseline |
| 5–6 | UI wireframes, API specs, infrastructure design reviews |
| 7–8 | Backend scaffolding, auth services, database schema, CI/CD bootstrap |
| 9–10 | Frontend messaging UI, WebSocket integration, baseline tests |
| 11–12 | Key management implementation, encryption workflow, secret storage |
| 13–14 | Real-time messaging hardening, offline delivery, attachment encryption |
| 15–16 | Security testing (SAST/DAST), performance tuning, telemetry setup |
| 17–18 | Bug bashes, documentation drafting, compliance checklist |
| 19–20 | Final integration, rehearsals, project report and presentation submission |

## 10. References
1. NIST SP 800-53 Rev.5 – Security and Privacy Controls for Information Systems and Organizations.
2. OWASP Top Ten (2021) – Awareness document for application security.
3. W3C Web Cryptography API Recommendation (January 2017).
4. OWASP Application Security Verification Standard (ASVS) v4.0.3.
5. Signal Protocol Documentation – Reference for double-ratchet-based secure messaging.
