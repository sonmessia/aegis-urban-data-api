"""Use case: List entities with optional filtering and pagination."""

from app.modules.entities.application.dtos import EntityDTO, EntityListDTO, ListEntitiesQuery
from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.domain.value_objects import EntityType


class ListEntitiesUseCase:
    """Orchestrates querying entities."""

    def __init__(self, repository: IEntityRepository) -> None:
        self._repository = repository

    async def execute(self, query: ListEntitiesQuery) -> EntityListDTO:
        entity_type = EntityType(query.entity_type) if query.entity_type else None
        offset = (query.page - 1) * query.page_size

        entities, total = await self._repository.list_entities(
            entity_type=entity_type,
            limit=query.page_size,
            offset=offset,
        )

        return EntityListDTO(
            items=[EntityDTO.from_domain(e) for e in entities],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )
