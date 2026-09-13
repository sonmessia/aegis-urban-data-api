"""Use case: Query time-series observations and latest readings."""

from app.modules.observations.application.dtos import (
    ObservationDTO,
    ObservationListDTO,
    QueryObservationsQuery,
)
from app.modules.observations.domain.repository import IObservationRepository


class QueryObservationsUseCase:
    """Orchestrates time-series queries for sensor observations."""

    def __init__(self, repository: IObservationRepository) -> None:
        self._repository = repository

    async def execute_query(self, query: QueryObservationsQuery) -> ObservationListDTO:
        offset = (query.page - 1) * query.page_size
        items, total = await self._repository.query(
            entity_id=query.entity_id,
            attribute_name=query.attribute_name,
            from_time=query.from_time,
            to_time=query.to_time,
            limit=query.page_size,
            offset=offset,
        )

        return ObservationListDTO(
            items=[ObservationDTO.from_domain(obs) for obs in items],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    async def get_latest(self, entity_id: str) -> list[ObservationDTO]:
        items = await self._repository.get_latest(entity_id)
        return [ObservationDTO.from_domain(obs) for obs in items]
