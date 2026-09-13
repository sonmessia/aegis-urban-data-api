"""Use case: Retrieve an entity by its business entity ID."""

from app.modules.entities.application.dtos import EntityDTO
from app.modules.entities.domain.exceptions import EntityNotFoundError
from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.domain.value_objects import EntityId


class GetEntityUseCase:
    """Orchestrates retrieving an entity by ID."""

    def __init__(self, repository: IEntityRepository) -> None:
        self._repository = repository

    async def execute(self, entity_id_str: str) -> EntityDTO:
        entity_id = EntityId(entity_id_str)
        entity = await self._repository.get_by_entity_id(entity_id)
        if entity is None:
            raise EntityNotFoundError(entity_id_str)

        return EntityDTO.from_domain(entity)
