"""Entity service — business logic layer between router and DB."""

import uuid
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.schemas.entity import EntityCreate, EntityListResponse, EntityResponse, EntityUpdate

logger = structlog.get_logger(__name__)


class EntityNotFoundError(Exception):
    """Raised when an entity is not found in the database."""

    def __init__(self, entity_id: str) -> None:
        self.entity_id = entity_id
        super().__init__(f"Entity not found: {entity_id}")


class EntityAlreadyExistsError(Exception):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_id: str) -> None:
        self.entity_id = entity_id
        super().__init__(f"Entity already exists: {entity_id}")


class EntityService:
    """CRUD operations for FIWARE NGSI-v2 entities."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: EntityCreate) -> EntityResponse:
        """Ingest a new IoT entity. Raises EntityAlreadyExistsError if ID exists."""
        existing = await self._db.scalar(
            select(Entity).where(Entity.entity_id == payload.id)
        )
        if existing is not None:
            raise EntityAlreadyExistsError(payload.id)

        entity = Entity(
            entity_id=payload.id,
            entity_type=payload.type,
            attributes={k: v.model_dump() for k, v in payload.attributes.items()},
        )
        self._db.add(entity)
        await self._db.flush()
        await self._db.refresh(entity)

        logger.info("entity created", entity_id=entity.entity_id, type=entity.entity_type)
        return EntityResponse.model_validate(entity)

    async def get_by_entity_id(self, entity_id: str) -> EntityResponse:
        """Retrieve a single entity by its FIWARE entity ID."""
        entity = await self._db.scalar(
            select(Entity).where(Entity.entity_id == entity_id)
        )
        if entity is None:
            raise EntityNotFoundError(entity_id)
        return EntityResponse.model_validate(entity)

    async def list_entities(
        self,
        entity_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> EntityListResponse:
        """List entities with optional type filter and pagination."""
        query = select(Entity)
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)

        total = await self._db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        entities = await self._db.scalars(
            query.offset((page - 1) * page_size).limit(page_size)
        )

        return EntityListResponse(
            total=total or 0,
            page=page,
            page_size=page_size,
            items=[EntityResponse.model_validate(e) for e in entities],
        )

    async def update(self, entity_id: str, payload: EntityUpdate) -> EntityResponse:
        """Partially update entity attributes (upsert — preserves unlisted attributes)."""
        entity = await self._db.scalar(
            select(Entity).where(Entity.entity_id == entity_id)
        )
        if entity is None:
            raise EntityNotFoundError(entity_id)

        # Merge new attributes over existing ones
        updated_attrs: dict[str, Any] = {**entity.attributes}
        updated_attrs.update({k: v.model_dump() for k, v in payload.attributes.items()})
        entity.attributes = updated_attrs

        await self._db.flush()
        await self._db.refresh(entity)

        logger.info("entity updated", entity_id=entity_id)
        return EntityResponse.model_validate(entity)

    async def delete(self, entity_id: str) -> None:
        """Delete an entity by its FIWARE entity ID."""
        entity = await self._db.scalar(
            select(Entity).where(Entity.entity_id == entity_id)
        )
        if entity is None:
            raise EntityNotFoundError(entity_id)
        await self._db.delete(entity)
        logger.info("entity deleted", entity_id=entity_id)
