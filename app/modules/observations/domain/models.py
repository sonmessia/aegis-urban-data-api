"""Domain model for IoT sensor observations (time-series telemetry)."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Observation:
    """
    Individual sensor metric observation at a point in time.

    Examples:
    - PM2.5 reading: 42.5 ug/m3 at 2026-09-13T10:00:00Z
    - Traffic speed: 55.0 km/h at 2026-09-13T10:00:00Z
    """

    entity_id: str
    attribute_name: str
    timestamp: datetime
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.entity_id:
            raise ValueError("Observation entity_id cannot be empty")
        if not self.attribute_name:
            raise ValueError("Observation attribute_name cannot be empty")
        if self.value_numeric is None and self.value_text is None:
            raise ValueError("Observation must contain either value_numeric or value_text")
