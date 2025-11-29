"""Database migration script to recreate tables with new schema."""

from app import create_app
from app.extensions import db
from app.models import Contact, Message, PublicKey, User

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✓ Database recreated with new schema")
    print("✓ Tables created: users, contacts, public_keys, messages")

