"""Use case: Update attributes of an existing entity."""

from app.modules.entities.application.dtos import EntityDTO, UpdateEntityCommand
from app.modules.entities.domain.exceptions import EntityNotFoundError
from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.domain.value_objects import EntityId


class UpdateEntityUseCase:
    """Orchestrates updating entity attributes."""

    def __init__(self, repository: IEntityRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateEntityCommand) -> EntityDTO:
        entity_id = EntityId(command.entity_id)
        entity = await self._repository.get_by_entity_id(entity_id)
        if entity is None:
            raise EntityNotFoundError(command.entity_id)

        entity.update_attributes(command.attributes)
        await self._repository.update(entity)

        return EntityDTO.from_domain(entity)
