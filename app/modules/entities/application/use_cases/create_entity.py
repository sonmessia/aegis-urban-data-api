"""Use case: Ingest and persist a new IoT entity."""

from app.modules.entities.application.dtos import CreateEntityCommand, EntityDTO
from app.modules.entities.domain.exceptions import EntityAlreadyExistsError
from app.modules.entities.domain.models import Entity
from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.domain.value_objects import EntityId, EntityType


class CreateEntityUseCase:
    """Orchestrates creating a new IoT entity."""

    def __init__(self, repository: IEntityRepository) -> None:
        self._repository = repository

    async def execute(self, command: CreateEntityCommand) -> EntityDTO:
        entity_id = EntityId(command.entity_id)
        entity_type = EntityType(command.entity_type)

        existing = await self._repository.get_by_entity_id(entity_id)
        if existing is not None:
            raise EntityAlreadyExistsError(command.entity_id)

        entity = Entity(
            entity_id=entity_id,
            entity_type=entity_type,
            attributes=command.attributes,
        )

        await self._repository.add(entity)
        return EntityDTO.from_domain(entity)
