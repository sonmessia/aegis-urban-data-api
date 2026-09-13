"""Application layer — Data Transfer Objects (DTOs)."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.modules.entities.domain.models import Entity


@dataclass(frozen=True)
class EntityDTO:
    """Output DTO representing an Entity."""

    id: uuid.UUID
    entity_id: str
    entity_type: str
    attributes: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, entity: Entity) -> "EntityDTO":
        return cls(
            id=entity.id,
            entity_id=str(entity.entity_id),
            entity_type=str(entity.entity_type),
            attributes=entity.attributes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


@dataclass(frozen=True)
class CreateEntityCommand:
    """Input command for creating an Entity."""

    entity_id: str
    entity_type: str
    attributes: dict[str, Any]


@dataclass(frozen=True)
class UpdateEntityCommand:
    """Input command for updating an Entity's attributes."""

    entity_id: str
    attributes: dict[str, Any]


@dataclass(frozen=True)
class ListEntitiesQuery:
    """Input query for listing entities."""

    entity_type: str | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class EntityListDTO:
    """Paginated output DTO."""

    items: list[EntityDTO]
    total: int
    page: int
    page_size: int
