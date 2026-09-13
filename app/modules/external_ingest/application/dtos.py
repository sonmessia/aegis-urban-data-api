"""Application DTOs for external data ingestion."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class StationSyncResult:
    station_id: str
    entity_id: str
    success: bool
    measurements: dict[str, Any]
    error: str | None = None


@dataclass(frozen=True)
class SyncSummaryDTO:
    timestamp: datetime
    stations_queried: int
    stations_updated: int
    observations_created: int
    results: list[StationSyncResult]
