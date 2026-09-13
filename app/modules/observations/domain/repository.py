"""Domain repository interface for Observations."""

from abc import ABC, abstractmethod
from datetime import datetime

from app.modules.observations.domain.models import Observation


class IObservationRepository(ABC):
    """Abstract repository for IoT observations."""

    @abstractmethod
    async def add_bulk(self, observations: list[Observation]) -> None:
        """Batch insert observations efficiently."""
        raise NotImplementedError

    @abstractmethod
    async def query(
        self,
        entity_id: str,
        attribute_name: str | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Observation], int]:
        """Query time-series observations."""
        raise NotImplementedError

    @abstractmethod
    async def get_latest(
        self,
        entity_id: str,
    ) -> list[Observation]:
        """Get the latest reading for each attribute of an entity."""
        raise NotImplementedError
