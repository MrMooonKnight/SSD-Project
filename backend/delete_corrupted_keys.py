"""Delete all corrupted public keys from the database."""

import re
from app import create_app
from app.extensions import db
from app.models import PublicKey

app = create_app()

with app.app_context():
    keys = PublicKey.query.all()
    deleted_count = 0
    
    for key in keys:
        # Check if key contains invalid characters
        cleaned = re.sub(r'-----BEGIN[^-]*-----', '', key.public_key_pem, flags=re.IGNORECASE)
        cleaned = re.sub(r'-----END[^-]*-----', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[\s\r\n\t]', '', cleaned)
        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', cleaned)
        
        # If key has invalid characters or doesn't match base64 pattern, delete it
        if not cleaned or not re.match(r'^[A-Za-z0-9+/]+={0,2}$', cleaned):
            print(f"Deleting corrupted key for user_id {key.user_id}")
            db.session.delete(key)
            deleted_count += 1
    
    db.session.commit()
    print(f"\nDeleted {deleted_count} corrupted keys")
    print("Users will need to log in again to regenerate their keys.")

