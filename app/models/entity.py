"""SQLAlchemy ORM model for IoT sensor entities (FIWARE NGSI-v2 inspired)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Entity(Base):
    """
    Represents a FIWARE NGSI-v2 entity (e.g., a sensor, vehicle, building).

    Schema aligns with NGSI-v2 simplified entity representation.
    Attributes stored as JSONB for flexible IoT payloads.
    """

    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
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
        JSONB,
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
        return f"<Entity id={self.entity_id!r} type={self.entity_type!r}>"
