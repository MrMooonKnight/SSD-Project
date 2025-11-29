"""Delete ALL public keys so users can regenerate them cleanly."""

from app import create_app
from app.extensions import db
from app.models import PublicKey

app = create_app()

with app.app_context():
    count = PublicKey.query.count()
    PublicKey.query.delete()
    db.session.commit()
    print(f"Deleted {count} public keys")
    print("All users will need to log in again to regenerate their keys.")

