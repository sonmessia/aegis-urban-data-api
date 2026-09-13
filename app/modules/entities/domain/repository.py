"""
Domain layer — Repository interface.

Defines the contract for persistence operations on Entity aggregates.
Implementations live in the infrastructure layer (e.g. PostgresEntityRepository).
"""

from abc import ABC, abstractmethod

from app.modules.entities.domain.models import Entity
from app.modules.entities.domain.value_objects import EntityId, EntityType


class IEntityRepository(ABC):
    """Abstract repository interface for Entity aggregates."""

    @abstractmethod
    async def add(self, entity: Entity) -> None:
        """Persist a new entity."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_entity_id(self, entity_id: EntityId) -> Entity | None:
        """Find an entity by its business entity ID."""
        raise NotImplementedError

    @abstractmethod
    async def list_entities(
        self,
        entity_type: EntityType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Entity], int]:
        """List entities with optional type filter and pagination. Returns (items, total_count)."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: Entity) -> None:
        """Update an existing entity."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity: Entity) -> None:
        """Delete an entity."""
        raise NotImplementedError
