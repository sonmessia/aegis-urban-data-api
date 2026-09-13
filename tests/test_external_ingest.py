"""Tests for External Ingest (Open-Meteo) module — domain, use case, and API tests."""

from datetime import UTC, datetime

import pytest
from app.main import create_app
from app.modules.entities.infrastructure.orm import EntityORM  # noqa: F401
from app.modules.entities.infrastructure.pg_repository import (
    PostgresEntityRepository,
)
from app.modules.external_ingest.application.use_cases.sync_public_data import (
    SyncPublicDataUseCase,
)
from app.modules.external_ingest.domain.client_interface import IOpenMeteoClient
from app.modules.external_ingest.domain.models import (
    AirQualitySnapshot,
    MergedStationReading,
    StationLocation,
    WeatherSnapshot,
    get_default_hcmc_stations,
)
from app.modules.observations.infrastructure.orm import ObservationORM  # noqa: F401
from app.modules.observations.infrastructure.pg_repository import (
    PostgresObservationRepository,
)
from app.shared.infrastructure.database import Base, get_db_session
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ─── Domain tests ─────────────────────────────────────────────────────────────


def test_station_location_and_fiware_mapping() -> None:
    station = StationLocation("HCM-D1", "District 1", 10.77, 106.70)
    assert station.entity_id == "urn:ngsi-v2:AirQualityObserved:HCM-D1"

    reading = MergedStationReading(
        station=station,
        timestamp=datetime.now(UTC),
        air_quality=AirQualitySnapshot(pm25=35.0, pm10=45.0, co=500.0, no2=20.0, o3=60.0),
        weather=WeatherSnapshot(temperature=29.5, humidity=80.0, pressure=1010.0, wind_speed=5.0),
    )

    attrs = reading.to_fiware_attributes()
    assert attrs["pm25"]["value"] == 35.0
    assert attrs["temperature"]["value"] == 29.5
    assert attrs["location"]["value"]["coordinates"] == [106.70, 10.77]
    assert "Open-Meteo" in attrs["dataProvider"]["value"]


# ─── Use Case tests with Mock Client ──────────────────────────────────────────


class MockOpenMeteoClient(IOpenMeteoClient):
    def __init__(self) -> None:
        self.call_count = 0

    async def fetch_reading(self, station: StationLocation) -> MergedStationReading | None:
        return MergedStationReading(
            station=station,
            timestamp=datetime.now(UTC),
            air_quality=AirQualitySnapshot(pm25=42.0, pm10=50.0, co=None, no2=None, o3=None),
            weather=WeatherSnapshot(
                temperature=30.0, humidity=75.0, pressure=None, wind_speed=None
            ),
        )

    async def fetch_all_readings(
        self, stations: list[StationLocation]
    ) -> list[MergedStationReading]:
        self.call_count += len(stations)
        return [
            MergedStationReading(
                station=s,
                timestamp=datetime.now(UTC),
                air_quality=AirQualitySnapshot(pm25=42.0, pm10=50.0, co=None, no2=None, o3=None),
                weather=WeatherSnapshot(
                    temperature=30.0, humidity=75.0, pressure=None, wind_speed=None
                ),
            )
            for s in stations
        ]


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db_session():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_sync_public_data_use_case(db_session: AsyncSession) -> None:
    mock_client = MockOpenMeteoClient()
    entity_repo = PostgresEntityRepository(db_session)
    obs_repo = PostgresObservationRepository(db_session)
    use_case = SyncPublicDataUseCase(mock_client, entity_repo, obs_repo)

    test_station = StationLocation("HCM-Test", "Test Station", 10.77, 106.70)
    summary = await use_case.execute([test_station])

    assert summary.stations_queried == 1
    assert summary.stations_updated == 1
    assert summary.observations_created >= 4
    assert len(summary.results) == 1
    assert summary.results[0].success is True
    assert summary.results[0].measurements["pm25"] == 42.0


# ─── API Integration tests ────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_list_stations_and_status(client: AsyncClient) -> None:
    # 1. List stations
    resp = await client.get("/v1/external-ingest/stations")
    assert resp.status_code == 200
    stations = resp.json()
    assert len(stations) == len(get_default_hcmc_stations())
    assert any(s["station_id"] == "HCM-District1-Center" for s in stations)

    # 2. Get status
    resp = await client.get("/v1/external-ingest/status")
    assert resp.status_code == 200
    status_data = resp.json()
    assert "is_running" in status_data
    assert status_data["monitored_stations_count"] >= 5
