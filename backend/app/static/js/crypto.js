// Web Crypto API wrapper for end-to-end encryption

class CryptoManager {
    constructor() {
        this.keyPair = null;
        this.contactKeys = new Map(); // email -> public key
        this.checkCryptoSupport();
    }

    checkCryptoSupport() {
        if (!window.crypto || !window.crypto.subtle) {
            const error = new Error('Web Crypto API is not available. This requires HTTPS or localhost.');
            console.error('Crypto API Error:', error.message);
            console.warn('To fix this:');
            console.warn('1. Access the app via https:// or http://localhost');
            console.warn('2. Or use a development server with SSL');
            alert('Web Crypto API is not available. Please access the app via HTTPS or localhost for encryption to work.');
            throw error;
        }
    }

    async generateKeyPair() {
        try {
            this.checkCryptoSupport();
            this.keyPair = await window.crypto.subtle.generateKey(
                {
                    name: "ECDH",
                    namedCurve: "P-256"
                },
                true,
                ["deriveKey", "deriveBits"]
            );
            return this.keyPair;
        } catch (error) {
            console.error('Error generating key pair:', error);
            throw error;
        }
    }

    async exportPublicKey(key) {
        this.checkCryptoSupport();
        const exported = await window.crypto.subtle.exportKey("spki", key);
        return this.arrayBufferToBase64(exported);
    }

    async importPublicKey(base64Key) {
        this.checkCryptoSupport();
        
        if (!base64Key || typeof base64Key !== 'string') {
            throw new Error('Invalid base64 key: must be a non-empty string');
        }
        
        // Final aggressive clean using character codes
        base64Key = base64Key.split('').filter(char => {
            const code = char.charCodeAt(0);
            return (code >= 65 && code <= 90) ||  // A-Z
                   (code >= 97 && code <= 122) || // a-z
                   (code >= 48 && code <= 57) ||  // 0-9
                   code === 43 ||                  // +
                   code === 47 ||                  // /
                   code === 61;                    // =
        }).join('');
        
        // Add padding
        const remainder = base64Key.length % 4;
        if (remainder !== 0) {
            base64Key += '='.repeat(4 - remainder);
        }
        
        try {
            const keyData = this.base64ToArrayBuffer(base64Key);
            
            // Validate key data size (ECDH P-256 public key should be ~91 bytes in SPKI format)
            // But allow some flexibility
            if (keyData.byteLength < 64 || keyData.byteLength > 200) {
                throw new Error(`Invalid key size: ${keyData.byteLength} bytes. Expected ~91 bytes for ECDH P-256 SPKI.`);
            }
            
            return await window.crypto.subtle.importKey(
                "spki",
                keyData,
                {
                    name: "ECDH",
                    namedCurve: "P-256"
                },
                true,
                ["deriveKey", "deriveBits"]
            );
        } catch (error) {
            if (error.message && (error.message.includes('Invalid key size') || error.message.includes('Invalid base64'))) {
                throw error;
            }
            // Provide more context about the error
            const errorMsg = error.message || String(error);
            if (errorMsg.includes('invalid') || errorMsg.includes('illegal')) {
                throw new Error(`Failed to import public key: The key data is invalid or corrupted. Key length: ${base64Key.length}, Decoded size: ${this.base64ToArrayBuffer(base64Key).byteLength} bytes. The contact needs to regenerate their key.`);
            }
            throw new Error(`Failed to import public key: ${errorMsg}`);
        }
    }

    async deriveSharedSecret(publicKey) {
        this.checkCryptoSupport();
        return await window.crypto.subtle.deriveBits(
            {
                name: "ECDH",
                public: publicKey
            },
            this.keyPair.privateKey,
            256
        );
    }

    async encryptMessage(message, recipientPublicKey) {
        try {
            // Derive shared secret
            const sharedSecret = await this.deriveSharedSecret(recipientPublicKey);
            
            // Derive encryption key from shared secret
            const keyMaterial = await window.crypto.subtle.importKey(
                "raw",
                sharedSecret,
                { name: "PBKDF2" },
                false,
                ["deriveBits", "deriveKey"]
            );

            const salt = window.crypto.getRandomValues(new Uint8Array(16));
            const key = await window.crypto.subtle.deriveKey(
                {
                    name: "PBKDF2",
                    salt: salt,
                    iterations: 100000,
                    hash: "SHA-256"
                },
                keyMaterial,
                { name: "AES-GCM", length: 256 },
                false,
                ["encrypt"]
            );

            // Encrypt message
            const iv = window.crypto.getRandomValues(new Uint8Array(12));
            const encodedMessage = new TextEncoder().encode(message);
            
            const ciphertext = await window.crypto.subtle.encrypt(
                {
                    name: "AES-GCM",
                    iv: iv
                },
                key,
                encodedMessage
            );

            return {
                ciphertext: this.arrayBufferToBase64(ciphertext),
                nonce: this.arrayBufferToBase64(iv),
                salt: this.arrayBufferToBase64(salt)
            };
        } catch (error) {
            console.error('Error encrypting message:', error);
            throw error;
        }
    }

    async decryptMessage(encryptedData, senderPublicKey) {
        try {
            // Derive shared secret
            const sharedSecret = await this.deriveSharedSecret(senderPublicKey);
            
            // Derive decryption key
            const keyMaterial = await window.crypto.subtle.importKey(
                "raw",
                sharedSecret,
                { name: "PBKDF2" },
                false,
                ["deriveBits", "deriveKey"]
            );

            const salt = this.base64ToArrayBuffer(encryptedData.salt);
            const key = await window.crypto.subtle.deriveKey(
                {
                    name: "PBKDF2",
                    salt: salt,
                    iterations: 100000,
                    hash: "SHA-256"
                },
                keyMaterial,
                { name: "AES-GCM", length: 256 },
                false,
                ["decrypt"]
            );

            // Decrypt message
            const iv = this.base64ToArrayBuffer(encryptedData.nonce);
            const ciphertext = this.base64ToArrayBuffer(encryptedData.ciphertext);
            
            const decrypted = await window.crypto.subtle.decrypt(
                {
                    name: "AES-GCM",
                    iv: iv
                },
                key,
                ciphertext
            );

            return new TextDecoder().decode(decrypted);
        } catch (error) {
            console.error('Error decrypting message:', error);
            throw error;
        }
    }

    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    base64ToArrayBuffer(base64) {
        // Validate and clean base64 string
        if (!base64 || typeof base64 !== 'string') {
            throw new Error('Invalid base64 input: must be a non-empty string');
        }
        
        // AGGRESSIVE cleaning - remove ALL non-base64 characters
        let cleaned = base64.trim();
        
        // Remove ALL characters that are NOT valid base64 using character codes
        cleaned = cleaned.split('').filter(char => {
            const code = char.charCodeAt(0);
            // Allow: A-Z (65-90), a-z (97-122), 0-9 (48-57), + (43), / (47), = (61)
            return (code >= 65 && code <= 90) ||  // A-Z
                   (code >= 97 && code <= 122) || // a-z
                   (code >= 48 && code <= 57) ||  // 0-9
                   code === 43 ||                  // +
                   code === 47 ||                  // /
                   code === 61;                    // =
        }).join('');
        
        // Validate base64 format
        if (cleaned.length === 0) {
            throw new Error('Empty base64 string after cleaning');
        }
        
        // Base64 should only contain A-Z, a-z, 0-9, +, /, and = for padding
        const base64Regex = /^[A-Za-z0-9+/]+={0,2}$/;
        if (!base64Regex.test(cleaned)) {
            const invalid = cleaned.match(/[^A-Za-z0-9+/=]/g);
            throw new Error(`Invalid base64 characters detected: ${invalid ? invalid.join(', ') : 'unknown'}`);
        }
        
        // Add padding if needed
        const remainder = cleaned.length % 4;
        if (remainder !== 0) {
            cleaned += '='.repeat(4 - remainder);
        }
        
        try {
            const binary = atob(cleaned);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                bytes[i] = binary.charCodeAt(i);
            }
            return bytes.buffer;
        } catch (error) {
            throw new Error(`Failed to decode base64: ${error.message}. Key length: ${cleaned.length}`);
        }
    }

    async storeKeyPair() {
        if (!this.keyPair) return;
        
        const publicKeyBase64 = await this.exportPublicKey(this.keyPair.publicKey);
        localStorage.setItem('public_key', publicKeyBase64);
        // Note: In production, private key should be encrypted with user password
        // For this demo, we'll keep it in memory only
    }

    async loadKeyPair() {
        const storedPublicKey = localStorage.getItem('public_key');
        if (storedPublicKey) {
            // In production, reconstruct key pair from stored data
            // For now, generate new one if not in memory
            if (!this.keyPair) {
                await this.generateKeyPair();
            }
        }
    }
}

// Global crypto manager instance
const cryptoManager = new CryptoManager();

