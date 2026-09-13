"""Use case: Bulk or single ingestion of sensor observations."""

from app.modules.observations.application.dtos import (
    IngestObservationItem,
    ObservationDTO,
)
from app.modules.observations.domain.models import Observation
from app.modules.observations.domain.repository import IObservationRepository


class IngestObservationsUseCase:
    """Orchestrates ingesting telemetry observations."""

    def __init__(self, repository: IObservationRepository) -> None:
        self._repository = repository

    async def execute(self, items: list[IngestObservationItem]) -> list[ObservationDTO]:
        observations = [
            Observation(
                entity_id=item.entity_id,
                attribute_name=item.attribute_name,
                timestamp=item.timestamp,
                value_numeric=item.value_numeric,
                value_text=item.value_text,
                unit=item.unit,
            )
            for item in items
        ]

        await self._repository.add_bulk(observations)
        return [ObservationDTO.from_domain(obs) for obs in observations]
