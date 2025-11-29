"""Check if a key in the database is valid."""

from app import create_app
from app.extensions import db
from app.models import PublicKey
import base64
import re

app = create_app()

with app.app_context():
    key = PublicKey.query.filter_by(user_id=2).first()
    if key:
        # Clean the key the same way the frontend does
        cleaned = re.sub(r'-----BEGIN[^-]*-----', '', key.public_key_pem, flags=re.IGNORECASE)
        cleaned = re.sub(r'-----END[^-]*-----', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', cleaned)
        remainder = len(cleaned) % 4
        if remainder:
            cleaned += '=' * (4 - remainder)
        
        try:
            decoded = base64.b64decode(cleaned)
            print(f'Key length: {len(cleaned)} chars, Decoded: {len(decoded)} bytes')
            print(f'First 10 bytes (hex): {" ".join([hex(b) for b in decoded[:10]])}')
            print(f'First byte is 0x30 (ASN.1 SEQUENCE): {decoded[0] == 0x30}')
            print(f'Key appears valid: {decoded[0] == 0x30 and len(decoded) == 91}')
        except Exception as e:
            print(f'Error decoding key: {e}')

