"""Postgres implementation of IEntityRepository using SQLAlchemy 2.0 AsyncSession."""

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entities.domain.models import Entity
from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.domain.value_objects import EntityId, EntityType
from app.modules.entities.infrastructure.orm import EntityORM

logger = structlog.get_logger(__name__)


class PostgresEntityRepository(IEntityRepository):
    """Repository implementation using SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: EntityORM) -> Entity:
        """Map ORM entity to pure domain Entity aggregate."""
        return Entity(
            id=orm.id,
            entity_id=EntityId(orm.entity_id),
            entity_type=EntityType(orm.entity_type),
            attributes=orm.attributes,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def add(self, entity: Entity) -> None:
        """Add new entity record to session."""
        orm = EntityORM(
            id=entity.id,
            entity_id=str(entity.entity_id),
            entity_type=str(entity.entity_type),
            attributes=entity.attributes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        entity.id = orm.id
        entity.created_at = orm.created_at
        entity.updated_at = orm.updated_at

    async def get_by_entity_id(self, entity_id: EntityId) -> Entity | None:
        """Query entity by entity_id string."""
        stmt = select(EntityORM).where(EntityORM.entity_id == str(entity_id))
        orm = await self._session.scalar(stmt)
        if orm is None:
            return None
        return self._to_domain(orm)

    async def list_entities(
        self,
        entity_type: EntityType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Entity], int]:
        """Query paginated entities with optional type filter."""
        query = select(EntityORM)
        if entity_type is not None:
            query = query.where(EntityORM.entity_type == str(entity_type))

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self._session.scalar(total_stmt) or 0

        entities_stmt = query.offset(offset).limit(limit)
        orms = await self._session.scalars(entities_stmt)

        return [self._to_domain(orm) for orm in orms], total

    async def update(self, entity: Entity) -> None:
        """Update existing entity record."""
        stmt = select(EntityORM).where(EntityORM.entity_id == str(entity.entity_id))
        orm = await self._session.scalar(stmt)
        if orm is not None:
            orm.attributes = entity.attributes
            orm.updated_at = entity.updated_at
            await self._session.flush()
            await self._session.refresh(orm)

    async def delete(self, entity: Entity) -> None:
        """Delete entity record."""
        stmt = select(EntityORM).where(EntityORM.entity_id == str(entity.entity_id))
        orm = await self._session.scalar(stmt)
        if orm is not None:
            await self._session.delete(orm)
            await self._session.flush()
