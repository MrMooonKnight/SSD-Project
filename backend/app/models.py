"""Database models for the secure chat application."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class User(db.Model):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    public_key: Mapped[Optional["PublicKey"]] = relationship("PublicKey", back_populates="user", uselist=False)
    sent_messages: Mapped[list["Message"]] = relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender"
    )
    received_messages: Mapped[list["Message"]] = relationship(
        "Message", foreign_keys="Message.recipient_id", back_populates="recipient"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class PublicKey(db.Model):
    """Public key storage for E2EE."""

    __tablename__ = "public_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    public_key_pem: Mapped[str] = mapped_column(Text, nullable=False)  # Base64-encoded public key
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hex
    algorithm: Mapped[str] = mapped_column(String(20), nullable=False, default="Ed25519")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="public_key")

    __table_args__ = (Index("idx_public_key_user_id", "user_id"),)

    def __repr__(self) -> str:
        return f"<PublicKey user_id={self.user_id} fingerprint={self.fingerprint[:16]}...>"


class Message(db.Model):
    """Encrypted message relay storage."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)  # Base64-encoded encrypted payload
    nonce: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # Encryption nonce if applicable
    message_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")  # text, attachment, etc.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")

    __table_args__ = (
        Index("idx_message_sender_recipient", "sender_id", "recipient_id"),
        Index("idx_message_recipient_created", "recipient_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message {self.id} from {self.sender_id} to {self.recipient_id}>"

