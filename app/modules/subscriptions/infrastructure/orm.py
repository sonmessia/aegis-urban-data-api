"""SQLAlchemy ORM table mapping for Subscriptions."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database import Base


class SubscriptionORM(Base):
    """Persistence model for FIWARE NGSI-v2 subscriptions."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    subscription_id: Mapped[str] = mapped_column(
        String(256),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="",
    )
    subject_entity_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    subject_entity_id_pattern: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
    watched_attributes: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    notification_url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    notification_headers: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        index=True,
    )
    notification_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_notification: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SubscriptionORM id={self.subscription_id!r} type={self.subject_entity_type!r}>"
