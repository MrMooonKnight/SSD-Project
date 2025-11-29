// Chat application logic

let socket = null;
let currentUser = null;
let currentContact = null;
let contacts = [];

const API_BASE = '/api';
const WS_URL = window.location.origin;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Setup event listeners first so UI works even if initialization fails
    try {
        setupEventListeners();
    } catch (setupError) {
        console.error('Failed to setup event listeners:', setupError);
    }

    // Then initialize app
    try {
        await initializeApp();
    } catch (error) {
        console.error('Initialization error:', error);
        // Only redirect to login if it's an auth error
        if (error.message && error.message.includes('401')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        }
    }
});

async function initializeApp() {
    try {
        // Get current user
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
            return;
        }

        // Trim token to remove any whitespace
        const cleanToken = token.trim();
        
        const userResponse = await fetch(`${API_BASE}/auth/me`, {
            headers: { 
                'Authorization': `Bearer ${cleanToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!userResponse.ok) {
            // Token might be expired, try refresh
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
                try {
                    const refreshResponse = await fetch(`${API_BASE}/auth/refresh`, {
                        method: 'POST',
                        headers: { 
                            'Authorization': `Bearer ${refreshToken.trim()}`,
                            'Content-Type': 'application/json'
                        }
                    });
                    if (refreshResponse.ok) {
                        const refreshData = await refreshResponse.json();
                        localStorage.setItem('access_token', refreshData.access_token);
                        // Retry getting user info
                        const retryResponse = await fetch(`${API_BASE}/auth/me`, {
                            headers: { 'Authorization': `Bearer ${refreshData.access_token}` }
                        });
                        if (retryResponse.ok) {
                            currentUser = await retryResponse.json();
                        } else {
                            throw new Error('Failed to get user after refresh');
                        }
                    } else {
                        throw new Error('Token refresh failed');
                    }
                } catch (refreshError) {
                    console.error('Token refresh error:', refreshError);
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                    return;
                }
            } else {
                localStorage.removeItem('access_token');
                window.location.href = '/login';
                return;
            }
        } else {
            currentUser = await userResponse.json();
        }

        document.getElementById('userEmail').textContent = currentUser.email;

        // Initialize crypto (only if available)
        try {
            await cryptoManager.loadKeyPair();
            if (!cryptoManager.keyPair) {
                await cryptoManager.generateKeyPair();
                await uploadPublicKey();
            } else {
                // Verify existing key is valid, regenerate if corrupted
                try {
                    const testExport = await cryptoManager.exportPublicKey(cryptoManager.keyPair.publicKey);
                    if (!testExport || !/^[A-Za-z0-9+/]+={0,2}$/.test(testExport)) {
                        console.warn('Existing key appears corrupted, regenerating...');
                        await cryptoManager.generateKeyPair();
                        await uploadPublicKey();
                    }
                } catch (keyError) {
                    console.warn('Existing key invalid, regenerating...', keyError);
                    await cryptoManager.generateKeyPair();
                    await uploadPublicKey();
                }
            }
        } catch (cryptoError) {
            console.warn('Crypto initialization failed:', cryptoError.message);
            console.warn('Encryption features will be disabled. Access via HTTPS or localhost to enable.');
            // Continue without crypto - app will still work but without encryption
        }

        // Load contacts
        await loadContacts();

        // Connect WebSocket (optional - won't break if it fails)
        connectWebSocket();
    } catch (error) {
        console.error('Initialization error:', error);
        // Don't throw - allow app to continue
    } finally {
        // Always setup event listeners so UI works even if initialization fails
        setupEventListeners();
    }
}

async function uploadPublicKey() {
    try {
        const publicKeyBase64 = await cryptoManager.exportPublicKey(cryptoManager.keyPair.publicKey);
        
        // Validate the key before uploading
        if (!publicKeyBase64 || !/^[A-Za-z0-9+/]+={0,2}$/.test(publicKeyBase64)) {
            console.error('Invalid public key format generated');
            throw new Error('Invalid public key format');
        }
        
        const response = await fetch(`${API_BASE}/keys/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                public_key: `-----BEGIN PUBLIC KEY-----\n${publicKeyBase64}\n-----END PUBLIC KEY-----`,
                algorithm: 'ECDH'
            })
        });

        if (!response.ok) {
            console.error('Failed to upload public key');
        }
    } catch (error) {
        console.error('Error uploading public key:', error);
    }
}

async function loadContacts() {
    try {
        const response = await fetch(`${API_BASE}/contacts/list`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });

        if (response.ok) {
            const data = await response.json();
            contacts = data.contacts;
            renderContacts();
        }
    } catch (error) {
        console.error('Error loading contacts:', error);
    }
}

function renderContacts() {
    const contactsList = document.getElementById('contactsList');
    contactsList.innerHTML = '';

    contacts.forEach(contact => {
        const contactDiv = document.createElement('div');
        contactDiv.className = 'contact-item';
        contactDiv.dataset.email = contact.email;
        contactDiv.innerHTML = `
            <h4>${contact.display_name || contact.email}</h4>
            <span>${contact.email}</span>
        `;
        contactDiv.addEventListener('click', () => selectContact(contact));
        contactsList.appendChild(contactDiv);
    });
}

async function selectContact(contact) {
    currentContact = contact;
    
    // Update UI
    document.querySelectorAll('.contact-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.email === contact.email) {
            item.classList.add('active');
        }
    });

    document.getElementById('noChatSelected').style.display = 'none';
    document.getElementById('chatWindow').style.display = 'flex';
    document.getElementById('chatContactName').textContent = contact.display_name || contact.email;
    document.getElementById('chatContactEmail').textContent = contact.email;

    // Load contact's public key (non-blocking - messages can still load)
    loadContactPublicKey(contact.email).catch(error => {
        console.warn('Could not load public key for contact:', error);
    });

    // Load messages
    await loadMessages(contact.email);
}

async function loadContactPublicKey(email) {
    try {
        const response = await fetch(`${API_BASE}/keys/email/${email}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
        });

        if (response.ok) {
            const data = await response.json();
            if (!data.public_key) {
                console.warn(`No public key found for ${email}`);
                return null;
            }

            // AGGRESSIVE cleaning - remove headers, footers, and ALL invalid characters
            let publicKeyPem = data.public_key;
            
            // Step 1: Remove PEM headers and footers (case insensitive, handle any variation)
            publicKeyPem = publicKeyPem.replace(/-----BEGIN[^-]*-----/gi, '');
            publicKeyPem = publicKeyPem.replace(/-----END[^-]*-----/gi, '');
            
            // AGGRESSIVE CLEAN - use character code filtering (most reliable)
            const originalKey = data.public_key;
            
            // Remove PEM headers/footers first
            let cleaned = originalKey.replace(/-----BEGIN[^-]*-----/gi, '');
            cleaned = cleaned.replace(/-----END[^-]*-----/gi, '');
            
            // Use character code filtering to remove EVERYTHING that's not valid base64
            publicKeyPem = cleaned.split('').filter(char => {
                const code = char.charCodeAt(0);
                // ONLY allow: A-Z (65-90), a-z (97-122), 0-9 (48-57), + (43), / (47), = (61)
                return (code >= 65 && code <= 90) ||  // A-Z
                       (code >= 97 && code <= 122) || // a-z
                       (code >= 48 && code <= 57) ||  // 0-9
                       code === 43 ||                  // +
                       code === 47 ||                  // /
                       code === 61;                    // =
            }).join('');
            
            // Log what was removed
            const removedChars = [];
            for (let i = 0; i < cleaned.length; i++) {
                const char = cleaned[i];
                const code = char.charCodeAt(0);
                const isValid = (code >= 65 && code <= 90) || (code >= 97 && code <= 122) ||
                               (code >= 48 && code <= 57) || code === 43 || code === 47 || code === 61;
                if (!isValid && removedChars.indexOf(char) === -1) {
                    removedChars.push(char);
                }
            }
            if (removedChars.length > 0) {
                console.warn(`[${email}] Removed invalid chars:`, removedChars);
            }
            
            // Validate we have something
            if (!publicKeyPem || publicKeyPem.length === 0) {
                console.error(`[${email}] Empty key after cleaning`);
                return null;
            }
            
            // Add padding if needed
            const remainder = publicKeyPem.length % 4;
            if (remainder !== 0) {
                publicKeyPem += '='.repeat(4 - remainder);
            }
            
            // Final validation - should NEVER fail if cleaning worked
            if (!/^[A-Za-z0-9+/]+={0,2}$/.test(publicKeyPem)) {
                const invalid = publicKeyPem.match(/[^A-Za-z0-9+/=]/g);
                console.error(`[${email}] CRITICAL: Invalid chars after cleaning:`, invalid);
                return null;
            }
            
            // Check crypto availability
            if (!window.crypto || !window.crypto.subtle) {
                console.warn('Web Crypto API not available');
                return null;
            }
            
            try {
                // Import the cleaned key
                const publicKey = await cryptoManager.importPublicKey(publicKeyPem);
                cryptoManager.contactKeys.set(email, publicKey);
                console.log(`[${email}] Successfully loaded public key`);
                return publicKey;
            } catch (importError) {
                console.error(`[${email}] Import error:`, importError.message);
                console.error(`[${email}] Key length: ${publicKeyPem.length}`);
                
                // Verify no invalid chars (this should NEVER find any)
                const invalid = publicKeyPem.match(/[^A-Za-z0-9+/=]/g);
                if (invalid) {
                    console.error(`[${email}] BUG: Invalid chars in cleaned key:`, invalid);
                }
                
                return null;
            }
        } else if (response.status === 404) {
            console.warn(`Public key not found for user ${email}`);
            return null;
        } else {
            console.error(`Failed to load public key: ${response.status}`);
            return null;
        }
    } catch (error) {
        console.error('Error loading contact public key:', error);
        return null;
    }
}

async function loadMessages(contactEmail) {
    try {
        // Load both inbox and sent messages
        const [inboxRes, sentRes] = await Promise.all([
            fetch(`${API_BASE}/messages/inbox?limit=100`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            }),
            fetch(`${API_BASE}/messages/sent?limit=100`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
            })
        ]);

        let messages = [];
        
        if (inboxRes.ok) {
            const inboxData = await inboxRes.json();
            messages = messages.concat(inboxData.messages.filter(msg => 
                msg.sender_email === contactEmail
            ));
        }
        
        if (sentRes.ok) {
            const sentData = await sentRes.json();
            messages = messages.concat(sentData.messages.filter(msg => 
                msg.recipient_email === contactEmail
            ));
        }

        // Sort by created_at
        messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        
        renderMessages(messages);
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

async function renderMessages(messages) {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';

    for (const msg of messages) {
        const isSent = msg.sender_email === currentUser.email;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isSent ? 'sent' : 'received'}`;
        
        try {
            // Decrypt message
            if (isSent) {
                // For sent messages, we can't decrypt (would need recipient's private key)
                // In a real implementation, we'd store a local copy
                messageDiv.textContent = '[Sent message]';
            } else {
                const senderPublicKey = cryptoManager.contactKeys.get(msg.sender_email);
                if (senderPublicKey && msg.salt) {
                    try {
                        const decrypted = await cryptoManager.decryptMessage({
                            ciphertext: msg.ciphertext,
                            nonce: msg.nonce,
                            salt: msg.salt
                        }, senderPublicKey);
                        messageDiv.textContent = decrypted;
                    } catch (error) {
                        console.error('Decryption error:', error);
                        messageDiv.textContent = '[Unable to decrypt]';
                    }
                } else {
                    messageDiv.textContent = '[Encrypted - key not available]';
                }
            }
        } catch (error) {
            console.error('Decryption error:', error);
            messageDiv.textContent = '[Unable to decrypt]';
        }

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date(msg.created_at).toLocaleTimeString();
        messageDiv.appendChild(timeDiv);

        container.appendChild(messageDiv);
    }

    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || !currentContact) return;

    try {
        // Check if crypto is available
        if (!window.crypto || !window.crypto.subtle) {
            alert('Encryption is not available. Please access the app via HTTPS or localhost.');
            return;
        }

        // Get recipient's public key
        let recipientKey = cryptoManager.contactKeys.get(currentContact.email);
        if (!recipientKey) {
            recipientKey = await loadContactPublicKey(currentContact.email);
        }

        if (!recipientKey) {
            // Try one more time to load the key
            console.log('Attempting to reload public key for', currentContact.email);
            recipientKey = await loadContactPublicKey(currentContact.email);
            
            if (!recipientKey) {
                alert(`Recipient public key not available for ${currentContact.email}.\n\nPossible reasons:\n1. They haven't logged in yet to generate a key\n2. Their key is corrupted and needs to be regenerated\n3. Encryption is not available in this browser\n\nPlease ask them to log in and try again.`);
                return;
            }
        }

        // Encrypt message
        let encrypted;
        try {
            encrypted = await cryptoManager.encryptMessage(message, recipientKey);
        } catch (encryptError) {
            console.error('Encryption error:', encryptError);
            alert('Failed to encrypt message. Please try again.');
            return;
        }

        // Send to server
        const response = await fetch(`${API_BASE}/messages/send`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                recipient: currentContact.email,
                ciphertext: encrypted.ciphertext,
                nonce: encrypted.nonce,
                salt: encrypted.salt
            })
        });

        if (response.ok) {
            input.value = '';
            // Reload messages
            await loadMessages(currentContact.email);
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message');
    }
}

function connectWebSocket() {
    // Check if Socket.IO is available
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded. Real-time features will be disabled.');
        console.warn('This is usually due to CORS/CORP security headers blocking the CDN.');
        return;
    }

    try {
        socket = io(WS_URL, {
            auth: {
                token: localStorage.getItem('access_token')
            }
        });

        socket.on('connect', () => {
            console.log('WebSocket connected');
        });

        socket.on('new_message', async (data) => {
            if (currentContact && data.sender_email === currentContact.email) {
                await loadMessages(currentContact.email);
            }
        });

        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
        });
    } catch (error) {
        console.error('WebSocket connection error:', error);
    }
}

function setupEventListeners() {
    // Send message
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // Add contact button
    const addContactBtn = document.getElementById('addContactBtn');
    if (addContactBtn) {
        console.log('Add contact button found, attaching event listener');
        addContactBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Add contact button clicked');
            const modal = document.getElementById('addContactModal');
            if (modal) {
                console.log('Opening add contact modal');
                modal.style.display = 'flex';
                // Clear any previous errors
                const errorDiv = document.getElementById('contactError');
                if (errorDiv) errorDiv.textContent = '';
            } else {
                console.error('Add contact modal not found');
            }
        });
    } else {
        console.error('Add contact button not found in DOM');
    }

    // Add contact form submission
    const addContactForm = document.getElementById('addContactForm');
    if (addContactForm) {
        addContactForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const emailInput = document.getElementById('contactEmail');
            const email = emailInput ? emailInput.value.trim().toLowerCase() : '';
            const errorDiv = document.getElementById('contactError');
            
            if (!email) {
                if (errorDiv) errorDiv.textContent = 'Please enter an email address';
                return;
            }

            if (errorDiv) errorDiv.textContent = '';

            try {
                const token = localStorage.getItem('access_token');
                if (!token) {
                    window.location.href = '/login';
                    return;
                }

                const response = await fetch(`${API_BASE}/contacts/add`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token.trim()}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email })
                });

                const data = await response.json();

                if (response.ok) {
                    const modal = document.getElementById('addContactModal');
                    if (modal) modal.style.display = 'none';
                    if (addContactForm) addContactForm.reset();
                    await loadContacts();
                } else {
                    if (errorDiv) {
                        errorDiv.textContent = data.error || 'Failed to add contact';
                    }
                }
            } catch (error) {
                console.error('Error adding contact:', error);
                if (errorDiv) errorDiv.textContent = 'Network error. Please try again.';
            }
        });
    }

    // Close modal
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('addContactModal').style.display = 'none';
            document.getElementById('addContactForm').reset();
            document.getElementById('contactError').textContent = '';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('addContactModal');
        if (e.target === modal) {
            modal.style.display = 'none';
            document.getElementById('addContactForm').reset();
            document.getElementById('contactError').textContent = '';
        }
    });

    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        });
    }
}

