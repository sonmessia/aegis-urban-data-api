"""SQLAlchemy ORM table mapping for Observations time-series."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.database import Base


class ObservationORM(Base):
    """
    Time-series observations storage.

    Optimized for time-range window queries and latest metric lookups.
    """

    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    entity_id: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        index=True,
    )
    attribute_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    value_numeric: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    value_text: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    unit: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_obs_entity_attr_time", "entity_id", "attribute_name", "timestamp"),
        Index("ix_obs_entity_time", "entity_id", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<ObservationORM entity={self.entity_id!r} attr={self.attribute_name!r} val={self.value_numeric}>"
