"""Script to clean up corrupted public keys in the database."""

import re
from app import create_app
from app.extensions import db
from app.models import PublicKey

app = create_app()

with app.app_context():
    keys = PublicKey.query.all()
    cleaned_count = 0
    deleted_count = 0
    
    for key in keys:
        original = key.public_key_pem
        # Remove PEM headers/footers
        cleaned = re.sub(r'-----BEGIN[^-]*-----', '', original, flags=re.IGNORECASE)
        cleaned = re.sub(r'-----END[^-]*-----', '', cleaned, flags=re.IGNORECASE)
        # Remove ALL non-base64 characters
        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', cleaned)
        
        # Validate it's proper base64
        if not cleaned or not re.match(r'^[A-Za-z0-9+/]+={0,2}$', cleaned):
            print(f"Deleting corrupted key for user_id {key.user_id} (invalid format)")
            db.session.delete(key)
            deleted_count += 1
        elif cleaned != original.replace('-----BEGIN PUBLIC KEY-----', '').replace('-----END PUBLIC KEY-----', '').replace('\n', '').replace(' ', ''):
            # Reconstruct clean PEM
            key.public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{cleaned}\n-----END PUBLIC KEY-----"
            cleaned_count += 1
            print(f"Cleaned key for user_id {key.user_id}")
    
    db.session.commit()
    print(f"\nCleaned {cleaned_count} keys, deleted {deleted_count} corrupted keys")


