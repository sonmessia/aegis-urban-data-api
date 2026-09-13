"""Background scheduler for periodic synchronization with Open-Meteo."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog

from app.modules.entities.infrastructure.pg_repository import (
    PostgresEntityRepository,
)
from app.modules.external_ingest.application.use_cases.sync_public_data import (
    SyncPublicDataUseCase,
)
from app.modules.external_ingest.domain.models import get_default_hcmc_stations
from app.modules.external_ingest.infrastructure.open_meteo_client import (
    OpenMeteoClient,
)
from app.modules.observations.infrastructure.pg_repository import (
    PostgresObservationRepository,
)
from app.shared.infrastructure.database import sessionmanager

logger = structlog.get_logger(__name__)


class PublicDataScheduler:
    """Manages periodic background fetching from external public APIs."""

    def __init__(self) -> None:
        self._running: bool = False
        self._task: asyncio.Task[None] | None = None
        self._interval_minutes: int = 10
        self._last_sync_at: datetime | None = None
        self._total_syncs_completed: int = 0
        self._last_observations_count: int = 0

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    def get_status(self) -> dict[str, Any]:
        return {
            "is_running": self.is_running,
            "interval_minutes": self._interval_minutes,
            "last_sync_at": self._last_sync_at,
            "total_syncs_completed": self._total_syncs_completed,
            "last_observations_count": self._last_observations_count,
            "monitored_stations_count": len(get_default_hcmc_stations()),
        }

    async def start(self, interval_minutes: int = 10) -> None:
        if self.is_running:
            return

        self._interval_minutes = max(1, interval_minutes)
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("public data scheduler started", interval_minutes=self._interval_minutes)

    async def stop(self) -> None:
        if not self.is_running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("public data scheduler stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self.trigger_sync_now()
                await asyncio.sleep(self._interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("error during scheduled public data sync", error=str(exc))
                await asyncio.sleep(60)

    async def trigger_sync_now(self) -> int:
        """Trigger an immediate synchronization cycle."""
        client = OpenMeteoClient()
        async with sessionmanager.session() as session:
            entity_repo = PostgresEntityRepository(session)
            obs_repo = PostgresObservationRepository(session)
            use_case = SyncPublicDataUseCase(client, entity_repo, obs_repo)

            summary = await use_case.execute()
            self._last_sync_at = datetime.now(UTC)
            self._total_syncs_completed += 1
            self._last_observations_count = summary.observations_created
            return summary.observations_created


public_data_scheduler = PublicDataScheduler()
