"""FastAPI router for Entities endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.modules.entities.application.dtos import ListEntitiesQuery
from app.modules.entities.application.use_cases.create_entity import CreateEntityUseCase
from app.modules.entities.application.use_cases.delete_entity import DeleteEntityUseCase
from app.modules.entities.application.use_cases.get_entity import GetEntityUseCase
from app.modules.entities.application.use_cases.list_entities import ListEntitiesUseCase
from app.modules.entities.application.use_cases.update_entity import UpdateEntityUseCase
from app.modules.entities.domain.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
)
from app.modules.entities.presentation.dependencies import (
    get_create_entity_use_case,
    get_delete_entity_use_case,
    get_entity_use_case,
    get_list_entities_use_case,
    get_update_entity_use_case,
)
from app.modules.entities.presentation.schemas import (
    EntityCreateRequest,
    EntityListResponse,
    EntityResponse,
    EntityUpdateRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post(
    "",
    summary="Ingest IoT entity",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_entity(
    payload: EntityCreateRequest,
    use_case: CreateEntityUseCase = Depends(get_create_entity_use_case),
) -> EntityResponse:
    """Ingest a new FIWARE NGSI-v2 entity from an IoT sensor."""
    try:
        dto = await use_case.execute(payload.to_command())
        return EntityResponse.from_dto(dto)
    except EntityAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    summary="List entities",
    response_model=EntityListResponse,
)
async def list_entities(
    entity_type: str | None = Query(default=None, description="Filter by FIWARE entity type"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    use_case: ListEntitiesUseCase = Depends(get_list_entities_use_case),
) -> EntityListResponse:
    """List all ingested entities with optional type filter and pagination."""
    query = ListEntitiesQuery(entity_type=entity_type, page=page, page_size=page_size)
    dto = await use_case.execute(query)
    return EntityListResponse.from_dto(dto)


@router.get(
    "/{entity_id:path}",
    summary="Get entity by ID",
    response_model=EntityResponse,
)
async def get_entity(
    entity_id: str,
    use_case: GetEntityUseCase = Depends(get_entity_use_case),
) -> EntityResponse:
    """Retrieve a single entity by its FIWARE entity ID."""
    try:
        dto = await use_case.execute(entity_id)
        return EntityResponse.from_dto(dto)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{entity_id:path}",
    summary="Update entity attributes",
    response_model=EntityResponse,
)
async def update_entity(
    entity_id: str,
    payload: EntityUpdateRequest,
    use_case: UpdateEntityUseCase = Depends(get_update_entity_use_case),
) -> EntityResponse:
    """Partially update entity attributes."""
    try:
        dto = await use_case.execute(payload.to_command(entity_id))
        return EntityResponse.from_dto(dto)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{entity_id:path}",
    summary="Delete entity",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_entity(
    entity_id: str,
    use_case: DeleteEntityUseCase = Depends(get_delete_entity_use_case),
) -> None:
    """Delete an entity by its FIWARE entity ID."""
    try:
        await use_case.execute(entity_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
