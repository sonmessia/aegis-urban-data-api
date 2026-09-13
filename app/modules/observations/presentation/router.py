"""FastAPI router for Observations telemetry endpoints."""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, Query, status

from app.modules.observations.application.dtos import QueryObservationsQuery
from app.modules.observations.application.use_cases.ingest_observations import (
    IngestObservationsUseCase,
)
from app.modules.observations.application.use_cases.query_observations import (
    QueryObservationsUseCase,
)
from app.modules.observations.presentation.dependencies import (
    get_ingest_observations_use_case,
    get_query_observations_use_case,
)
from app.modules.observations.presentation.schemas import (
    ObservationBulkIn,
    ObservationIn,
    ObservationListResponse,
    ObservationResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/observations", tags=["observations"])


@router.post(
    "",
    summary="Ingest observation",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_observation(
    payload: ObservationIn,
    use_case: IngestObservationsUseCase = Depends(get_ingest_observations_use_case),
) -> ObservationResponse:
    """Ingest a single telemetry reading."""
    results = await use_case.execute([payload.to_item()])
    return ObservationResponse.from_dto(results[0])


@router.post(
    "/bulk",
    summary="Bulk ingest observations",
    response_model=list[ObservationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def ingest_observations_bulk(
    payload: ObservationBulkIn,
    use_case: IngestObservationsUseCase = Depends(get_ingest_observations_use_case),
) -> list[ObservationResponse]:
    """High-throughput batch ingestion for IoT sensor arrays."""
    items = [obs.to_item() for obs in payload.observations]
    results = await use_case.execute(items)
    return [ObservationResponse.from_dto(r) for r in results]


@router.get(
    "",
    summary="Query time-series observations",
    response_model=ObservationListResponse,
)
async def query_observations(
    entity_id: str = Query(..., description="Target FIWARE Entity ID"),
    attribute_name: str | None = Query(
        default=None, description="Optional attribute filter (e.g. pm25)"
    ),
    from_time: datetime | None = Query(default=None, description="Start timestamp (ISO-8601)"),
    to_time: datetime | None = Query(default=None, description="End timestamp (ISO-8601)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000),
    use_case: QueryObservationsUseCase = Depends(get_query_observations_use_case),
) -> ObservationListResponse:
    query = QueryObservationsQuery(
        entity_id=entity_id,
        attribute_name=attribute_name,
        from_time=from_time,
        to_time=to_time,
        page=page,
        page_size=page_size,
    )
    dto = await use_case.execute_query(query)
    return ObservationListResponse.from_dto(dto)


@router.get(
    "/latest",
    summary="Get latest observations for entity",
    response_model=list[ObservationResponse],
)
async def get_latest_observations(
    entity_id: str = Query(..., description="Target FIWARE Entity ID"),
    use_case: QueryObservationsUseCase = Depends(get_query_observations_use_case),
) -> list[ObservationResponse]:
    """Retrieve the most recent reading for each attribute of the entity."""
    results = await use_case.get_latest(entity_id)
    return [ObservationResponse.from_dto(r) for r in results]
