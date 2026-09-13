"""Abstract interface for external Open-Meteo public data provider."""

from abc import ABC, abstractmethod

from app.modules.external_ingest.domain.models import (
    MergedStationReading,
    StationLocation,
)


class IOpenMeteoClient(ABC):
    """Port for querying Open-Meteo public APIs."""

    @abstractmethod
    async def fetch_reading(self, station: StationLocation) -> MergedStationReading | None:
        """Fetch current weather and air quality for a single station."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_all_readings(
        self, stations: list[StationLocation]
    ) -> list[MergedStationReading]:
        """Fetch readings for multiple stations concurrently."""
        raise NotImplementedError
