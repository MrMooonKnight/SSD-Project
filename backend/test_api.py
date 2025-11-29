"""Simple script to test the VibeChat API endpoints."""

import json
import requests
from typing import Optional

BASE_URL = "http://localhost:5000/api"


class VibeChatClient:
    """Simple client for testing the VibeChat API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def register(self, username: str, password: str, display_name: Optional[str] = None) -> dict:
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={"username": username, "password": password, "display_name": display_name},
        )
        data = response.json()
        if response.status_code == 201:
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
        return data

    def login(self, username: str, password: str) -> dict:
        """Login and get tokens."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password},
        )
        data = response.json()
        if response.status_code == 200:
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
        return data

    def get_me(self) -> dict:
        """Get current user info."""
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        return response.json()

    def upload_public_key(self, public_key: str, algorithm: str = "Ed25519") -> dict:
        """Upload public key."""
        response = requests.post(
            f"{self.base_url}/keys/upload",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"public_key": public_key, "algorithm": algorithm},
        )
        return response.json()

    def get_public_key(self, username: str) -> dict:
        """Get public key by username."""
        response = requests.get(
            f"{self.base_url}/keys/{username}",
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        return response.json()

    def send_message(self, recipient: str, ciphertext: str, nonce: Optional[str] = None) -> dict:
        """Send encrypted message."""
        response = requests.post(
            f"{self.base_url}/messages/send",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"recipient": recipient, "ciphertext": ciphertext, "nonce": nonce},
        )
        return response.json()

    def get_inbox(self, limit: int = 50, offset: int = 0) -> dict:
        """Get received messages."""
        response = requests.get(
            f"{self.base_url}/messages/inbox",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params={"limit": limit, "offset": offset},
        )
        return response.json()

    def get_sent(self, limit: int = 50, offset: int = 0) -> dict:
        """Get sent messages."""
        response = requests.get(
            f"{self.base_url}/messages/sent",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params={"limit": limit, "offset": offset},
        )
        return response.json()


def print_response(title: str, response: dict):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(response, indent=2))


def main():
    """Test the API endpoints."""
    print("VibeChat API Test Script")
    print("=" * 60)

    # Create clients for two users
    alice = VibeChatClient()
    bob = VibeChatClient()

    try:
        # Test 1: Register users
        print("\n[1] Registering Alice...")
        print_response("Alice Registration", alice.register("alice", "password123", "Alice"))

        print("\n[2] Registering Bob...")
        print_response("Bob Registration", bob.register("bob", "password456", "Bob"))

        # Test 2: Login
        print("\n[3] Alice logging in...")
        print_response("Alice Login", alice.login("alice", "password123"))

        print("\n[4] Bob logging in...")
        print_response("Bob Login", bob.login("bob", "password456"))

        # Test 3: Get current user
        print("\n[5] Getting Alice's profile...")
        print_response("Alice Profile", alice.get_me())

        # Test 4: Upload public keys
        print("\n[6] Alice uploading public key...")
        alice_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"
        print_response("Alice Public Key Upload", alice.upload_public_key(alice_key))

        print("\n[7] Bob uploading public key...")
        bob_key = "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEB...\n-----END PUBLIC KEY-----"
        print_response("Bob Public Key Upload", bob.upload_public_key(bob_key))

        # Test 5: Get public keys
        print("\n[8] Alice fetching Bob's public key...")
        print_response("Bob's Public Key", alice.get_public_key("bob"))

        # Test 6: Send messages
        print("\n[9] Alice sending message to Bob...")
        ciphertext = "dGVzdC1lbmNyeXB0ZWQtbWVzc2FnZQ=="  # base64 encoded test message
        print_response("Message Sent", alice.send_message("bob", ciphertext, "nonce123"))

        # Test 7: Get inbox
        print("\n[10] Bob checking inbox...")
        print_response("Bob's Inbox", bob.get_inbox())

        # Test 8: Get sent messages
        print("\n[11] Alice checking sent messages...")
        print_response("Alice's Sent Messages", alice.get_sent())

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server.")
        print("Make sure the Flask server is running on http://localhost:5000")
        print("\nStart the server with:")
        print("  cd backend")
        print("  python run.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

