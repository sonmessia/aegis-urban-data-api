"""Application service for running and controlling IoT stream simulations."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog

from app.modules.entities.domain.models import Entity
from app.modules.entities.domain.value_objects import EntityId, EntityType
from app.modules.observations.domain.models import Observation
from app.modules.simulation.domain.sensors import (
    BaseSensor,
    get_default_urban_sensor_fleet,
)
from app.shared.infrastructure.database import sessionmanager

logger = structlog.get_logger(__name__)


class SimulationManager:
    """Singleton manager controlling ongoing IoT stream simulation."""

    def __init__(self) -> None:
        self._running: bool = False
        self._task: asyncio.Task[None] | None = None
        self._fleet: list[BaseSensor] = get_default_urban_sensor_fleet()
        self._sample_interval: float = 1.0  # seconds between sensor sweeps
        self._metrics_emitted_total: int = 0
        self._started_at: datetime | None = None

    @property
    def is_running(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    def get_status(self) -> dict[str, Any]:
        uptime_seconds = (
            (datetime.now(UTC) - self._started_at).total_seconds()
            if self._started_at and self.is_running
            else 0
        )
        return {
            "is_running": self.is_running,
            "fleet_size": len(self._fleet),
            "sample_interval_seconds": self._sample_interval,
            "metrics_emitted_total": self._metrics_emitted_total,
            "uptime_seconds": round(uptime_seconds, 1),
            "started_at": self._started_at,
        }

    async def seed_fleet(self) -> int:
        """Seed default sensor entities into database if they do not exist."""
        from app.modules.entities.infrastructure.pg_repository import (
            PostgresEntityRepository,
        )

        seeded_count = 0
        async with sessionmanager.session() as session:
            repo = PostgresEntityRepository(session)
            for sensor in self._fleet:
                existing = await repo.get_by_entity_id(EntityId(sensor.sensor_id))
                if existing is None:
                    attrs, _ = sensor.sample()
                    entity = Entity(
                        entity_id=EntityId(sensor.sensor_id),
                        entity_type=EntityType(sensor.entity_type),
                        attributes=attrs,
                    )
                    await repo.add(entity)
                    seeded_count += 1

        logger.info("fleet seeded", seeded_count=seeded_count, fleet_size=len(self._fleet))
        return seeded_count

    async def start(self, sample_interval: float = 1.0) -> None:
        if self.is_running:
            return

        self._sample_interval = max(0.1, sample_interval)
        self._running = True
        self._started_at = datetime.now(UTC)
        self._task = asyncio.create_task(self._run_loop())
        logger.info("simulation started", interval=self._sample_interval, fleet=len(self._fleet))

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
        logger.info("simulation stopped", total_emitted=self._metrics_emitted_total)

    async def _run_loop(self) -> None:
        from app.modules.entities.infrastructure.pg_repository import (
            PostgresEntityRepository,
        )
        from app.modules.observations.infrastructure.pg_repository import (
            PostgresObservationRepository,
        )

        while self._running:
            try:
                start_time = asyncio.get_event_loop().time()
                batch_obs: list[Observation] = []

                async with sessionmanager.session() as session:
                    entity_repo = PostgresEntityRepository(session)
                    obs_repo = PostgresObservationRepository(session)

                    for sensor in self._fleet:
                        attrs, obs_list = sensor.sample()

                        # Update entity state
                        entity = await entity_repo.get_by_entity_id(EntityId(sensor.sensor_id))
                        if entity:
                            entity.update_attributes(attrs)
                            await entity_repo.update(entity)

                        # Accumulate observations
                        for o in obs_list:
                            batch_obs.append(
                                Observation(
                                    entity_id=o["entity_id"],
                                    attribute_name=o["attribute_name"],
                                    timestamp=o["timestamp"],
                                    value_numeric=o["value_numeric"],
                                    unit=o["unit"],
                                )
                            )

                    # Bulk insert observations
                    await obs_repo.add_bulk(batch_obs)

                self._metrics_emitted_total += len(batch_obs)

                # Maintain target interval
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_time = max(0.01, self._sample_interval - elapsed)
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("simulation cycle error", error=str(exc))
                await asyncio.sleep(1.0)


simulation_manager = SimulationManager()
