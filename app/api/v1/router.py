"""API v1 router — entities endpoints + health/readiness probes."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.entity import (
    EntityCreate,
    EntityListResponse,
    EntityResponse,
    EntityUpdate,
)
from app.services.entity_service import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    EntityService,
)

logger = structlog.get_logger(__name__)

api_router = APIRouter()


# ─── Health & readiness probes ────────────────────────────────────────────────

@api_router.get(
    "/health",
    tags=["observability"],
    summary="Liveness probe",
    response_model=dict,
)
async def health() -> dict:
    """Liveness probe — returns 200 if the process is alive."""
    return {"status": "ok"}


@api_router.get(
    "/ready",
    tags=["observability"],
    summary="Readiness probe",
    response_model=dict,
)
async def ready(db: AsyncSession = Depends(get_db_session)) -> dict:
    """
    Readiness probe — verifies DB connectivity.
    Returns 503 if the database is not reachable.
    Kubernetes uses this to gate traffic: pods not ready do not receive requests.
    """
    try:
        await db.execute(db.bind.dialect.statement_compiler.visit_true)  # type: ignore[attr-defined]
        return {"status": "ready", "db": "ok"}
    except Exception as exc:
        logger.warning("readiness check failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "db": "unreachable"},
        ) from exc


# ─── Entities CRUD ────────────────────────────────────────────────────────────

@api_router.post(
    "/entities",
    tags=["entities"],
    summary="Ingest IoT entity",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_entity(
    payload: EntityCreate,
    db: AsyncSession = Depends(get_db_session),
) -> EntityResponse:
    """
    Ingest a new FIWARE NGSI-v2 entity from an IoT sensor.
    Returns 409 if an entity with the same ID already exists.
    """
    svc = EntityService(db)
    try:
        return await svc.create(payload)
    except EntityAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Entity already exists: {exc.entity_id}",
        ) from exc


@api_router.get(
    "/entities",
    tags=["entities"],
    summary="List entities",
    response_model=EntityListResponse,
)
async def list_entities(
    entity_type: str | None = Query(default=None, description="Filter by FIWARE entity type"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
) -> EntityListResponse:
    """List all ingested entities with optional type filter and pagination."""
    svc = EntityService(db)
    return await svc.list_entities(entity_type=entity_type, page=page, page_size=page_size)


@api_router.get(
    "/entities/{entity_id:path}",
    tags=["entities"],
    summary="Get entity by ID",
    response_model=EntityResponse,
)
async def get_entity(
    entity_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> EntityResponse:
    """Retrieve a single entity by its FIWARE entity ID (e.g., urn:ngsi-v2:Sensor:001)."""
    svc = EntityService(db)
    try:
        return await svc.get_by_entity_id(entity_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity not found: {entity_id}",
        ) from exc


@api_router.patch(
    "/entities/{entity_id:path}",
    tags=["entities"],
    summary="Update entity attributes",
    response_model=EntityResponse,
)
async def update_entity(
    entity_id: str,
    payload: EntityUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> EntityResponse:
    """Partially update entity attributes. Unlisted attributes are preserved."""
    svc = EntityService(db)
    try:
        return await svc.update(entity_id, payload)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity not found: {entity_id}",
        ) from exc


@api_router.delete(
    "/entities/{entity_id:path}",
    tags=["entities"],
    summary="Delete entity",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_entity(
    entity_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete an entity by its FIWARE entity ID."""
    svc = EntityService(db)
    try:
        await svc.delete(entity_id)
    except EntityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity not found: {entity_id}",
        ) from exc
