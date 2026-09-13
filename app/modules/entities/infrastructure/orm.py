"""SQLAlchemy ORM table mapping for IoT sensor entities."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database import Base


class EntityORM(Base):
    """
    Persistence model for FIWARE NGSI-v2 entities.

    Separated from Domain model to keep domain pure and free of ORM baggage.
    Uses generic SQLAlchemy types with PostgreSQL JSONB variant for cross-DB compatibility.
    """

    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    entity_id: Mapped[str] = mapped_column(
        String(256),
        unique=True,
        nullable=False,
        index=True,
        comment="FIWARE entity ID (e.g., 'urn:ngsi-v2:Sensor:001')",
    )
    entity_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="FIWARE entity type (e.g., 'AirQualityObserved')",
    )
    attributes: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=dict,
        comment="NGSI-v2 attributes as JSON (value + metadata per attribute)",
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
        return f"<EntityORM id={self.entity_id!r} type={self.entity_type!r}>"
