"""Tests for Simulation and IoT Traffic Generator module."""

import pytest
from app.main import create_app
from app.modules.entities.infrastructure.orm import EntityORM  # noqa: F401
from app.modules.observations.infrastructure.orm import ObservationORM  # noqa: F401
from app.modules.simulation.domain.sensors import (
    AirQualitySensor,
    TrafficFlowSensor,
    get_default_urban_sensor_fleet,
)
from app.shared.infrastructure.database import Base, get_db_session
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def test_sensor_generators() -> None:
    fleet = get_default_urban_sensor_fleet()
    assert len(fleet) >= 5

    aq_sensor = AirQualitySensor("test-aq", {"lat": 10.7, "lng": 106.7})
    attrs, obs = aq_sensor.sample()
    assert "pm25" in attrs
    assert "temperature" in attrs
    assert len(obs) == 5

    traffic_sensor = TrafficFlowSensor("test-traffic", {"lat": 10.7, "lng": 106.7})
    attrs, obs = traffic_sensor.sample()
    assert "vehicleCount" in attrs
    assert "averageSpeed" in attrs
    assert len(obs) == 3


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
async def test_simulation_status_and_seed_api(client: AsyncClient) -> None:
    # 1. Status initially stopped
    resp = await client.get("/v1/simulation/status")
    assert resp.status_code == 200
    assert "is_running" in resp.json()
    assert resp.json()["fleet_size"] >= 5

    # 2. Stop when not running is safe
    resp = await client.post("/v1/simulation/stop")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Simulation stopped"
