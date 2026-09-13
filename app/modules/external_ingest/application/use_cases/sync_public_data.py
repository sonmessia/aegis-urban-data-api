"""Use case: Fetch live data from Open-Meteo and synchronize into Entities and Observations."""

from datetime import UTC, datetime
from typing import Any

import structlog

from app.modules.entities.domain.models import Entity
from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.domain.value_objects import EntityId, EntityType
from app.modules.external_ingest.application.dtos import (
    StationSyncResult,
    SyncSummaryDTO,
)
from app.modules.external_ingest.domain.client_interface import IOpenMeteoClient
from app.modules.external_ingest.domain.models import (
    MergedStationReading,
    StationLocation,
    get_default_hcmc_stations,
)
from app.modules.observations.domain.models import Observation
from app.modules.observations.domain.repository import IObservationRepository
from app.modules.subscriptions.infrastructure.event_handler import (
    handle_entity_changed,
)

logger = structlog.get_logger(__name__)


class SyncPublicDataUseCase:
    """Orchestrates synchronizing real-world measurements into the platform."""

    def __init__(
        self,
        client: IOpenMeteoClient,
        entity_repo: IEntityRepository,
        observation_repo: IObservationRepository,
    ) -> None:
        self._client = client
        self._entity_repo = entity_repo
        self._observation_repo = observation_repo

    async def execute(self, stations: list[StationLocation] | None = None) -> SyncSummaryDTO:
        target_stations = stations or get_default_hcmc_stations()
        readings = await self._client.fetch_all_readings(target_stations)

        sync_results: list[StationSyncResult] = []
        all_observations: list[Observation] = []
        updated_count = 0

        for reading in readings:
            entity_id = reading.station.entity_id
            attrs = reading.to_fiware_attributes()

            # 1. Upsert Entity
            existing_entity = await self._entity_repo.get_by_entity_id(EntityId(entity_id))
            if existing_entity is not None:
                existing_entity.update_attributes(attrs)
                await self._entity_repo.update(existing_entity)
            else:
                new_entity = Entity(
                    entity_id=EntityId(entity_id),
                    entity_type=EntityType("AirQualityObserved"),
                    attributes=attrs,
                )
                await self._entity_repo.add(new_entity)

            updated_count += 1

            # 2. Extract Observations for time-series table
            obs_list = self._extract_observations(reading)
            all_observations.extend(obs_list)

            # 3. Trigger background subscription notifications
            await handle_entity_changed(
                entity_id=entity_id,
                entity_type="AirQualityObserved",
                attributes=attrs,
                changed_attributes=list(attrs.keys()),
            )

            # Extract flattened metrics for summary
            measurements: dict[str, Any] = {
                "pm25": reading.air_quality.pm25,
                "pm10": reading.air_quality.pm10,
                "temperature": reading.weather.temperature,
                "humidity": reading.weather.humidity,
                "wind_speed": reading.weather.wind_speed,
            }
            sync_results.append(
                StationSyncResult(
                    station_id=reading.station.station_id,
                    entity_id=entity_id,
                    success=True,
                    measurements=measurements,
                )
            )

        # 4. Batch save observations
        if all_observations:
            await self._observation_repo.add_bulk(all_observations)

        logger.info(
            "public data sync completed",
            stations_queried=len(target_stations),
            updated=updated_count,
            observations=len(all_observations),
        )

        return SyncSummaryDTO(
            timestamp=datetime.now(UTC),
            stations_queried=len(target_stations),
            stations_updated=updated_count,
            observations_created=len(all_observations),
            results=sync_results,
        )

    def _extract_observations(self, reading: MergedStationReading) -> list[Observation]:
        obs: list[Observation] = []
        entity_id = reading.station.entity_id
        t = reading.timestamp

        if reading.air_quality.pm25 is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="pm25",
                    value_numeric=reading.air_quality.pm25,
                    unit="ug/m3",
                    timestamp=t,
                )
            )
        if reading.air_quality.pm10 is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="pm10",
                    value_numeric=reading.air_quality.pm10,
                    unit="ug/m3",
                    timestamp=t,
                )
            )
        if reading.air_quality.co is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="co",
                    value_numeric=reading.air_quality.co,
                    unit="ug/m3",
                    timestamp=t,
                )
            )
        if reading.air_quality.no2 is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="no2",
                    value_numeric=reading.air_quality.no2,
                    unit="ug/m3",
                    timestamp=t,
                )
            )
        if reading.air_quality.o3 is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="o3",
                    value_numeric=reading.air_quality.o3,
                    unit="ug/m3",
                    timestamp=t,
                )
            )
        if reading.weather.temperature is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="temperature",
                    value_numeric=reading.weather.temperature,
                    unit="CEL",
                    timestamp=t,
                )
            )
        if reading.weather.humidity is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="humidity",
                    value_numeric=reading.weather.humidity,
                    unit="P1",
                    timestamp=t,
                )
            )
        if reading.weather.pressure is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="atmosphericPressure",
                    value_numeric=reading.weather.pressure,
                    unit="A97",
                    timestamp=t,
                )
            )
        if reading.weather.wind_speed is not None:
            obs.append(
                Observation(
                    entity_id=entity_id,
                    attribute_name="windSpeed",
                    value_numeric=reading.weather.wind_speed,
                    unit="KMH",
                    timestamp=t,
                )
            )

        return obs
