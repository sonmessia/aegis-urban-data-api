"""FastAPI dependencies for Entities presentation layer."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entities.application.use_cases.create_entity import CreateEntityUseCase
from app.modules.entities.application.use_cases.delete_entity import DeleteEntityUseCase
from app.modules.entities.application.use_cases.get_entity import GetEntityUseCase
from app.modules.entities.application.use_cases.list_entities import ListEntitiesUseCase
from app.modules.entities.application.use_cases.update_entity import UpdateEntityUseCase
from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.infrastructure.pg_repository import PostgresEntityRepository
from app.shared.infrastructure.database import get_db_session


def get_entity_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IEntityRepository:
    """Dependency to provide IEntityRepository implementation."""
    return PostgresEntityRepository(session)


def get_create_entity_use_case(
    repo: IEntityRepository = Depends(get_entity_repository),
) -> CreateEntityUseCase:
    return CreateEntityUseCase(repo)


def get_entity_use_case(
    repo: IEntityRepository = Depends(get_entity_repository),
) -> GetEntityUseCase:
    return GetEntityUseCase(repo)


def get_list_entities_use_case(
    repo: IEntityRepository = Depends(get_entity_repository),
) -> ListEntitiesUseCase:
    return ListEntitiesUseCase(repo)


def get_update_entity_use_case(
    repo: IEntityRepository = Depends(get_entity_repository),
) -> UpdateEntityUseCase:
    return UpdateEntityUseCase(repo)


def get_delete_entity_use_case(
    repo: IEntityRepository = Depends(get_entity_repository),
) -> DeleteEntityUseCase:
    return DeleteEntityUseCase(repo)
