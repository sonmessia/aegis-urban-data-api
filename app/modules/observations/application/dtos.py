"""Application DTOs for Observations."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.observations.domain.models import Observation


@dataclass(frozen=True)
class ObservationDTO:
    id: uuid.UUID
    entity_id: str
    attribute_name: str
    timestamp: datetime
    value_numeric: float | None
    value_text: str | None
    unit: str | None
    created_at: datetime

    @classmethod
    def from_domain(cls, obs: Observation) -> "ObservationDTO":
        return cls(
            id=obs.id,
            entity_id=obs.entity_id,
            attribute_name=obs.attribute_name,
            timestamp=obs.timestamp,
            value_numeric=obs.value_numeric,
            value_text=obs.value_text,
            unit=obs.unit,
            created_at=obs.created_at,
        )


@dataclass(frozen=True)
class IngestObservationItem:
    entity_id: str
    attribute_name: str
    timestamp: datetime
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None


@dataclass(frozen=True)
class QueryObservationsQuery:
    entity_id: str
    attribute_name: str | None = None
    from_time: datetime | None = None
    to_time: datetime | None = None
    page: int = 1
    page_size: int = 100


@dataclass(frozen=True)
class ObservationListDTO:
    items: list[ObservationDTO]
    total: int
    page: int
    page_size: int
