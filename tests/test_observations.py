"""Tests for Observations module — domain unit tests and API integration tests."""

from datetime import UTC, datetime

import pytest
from app.main import create_app
from app.modules.observations.domain.models import Observation
from app.modules.observations.infrastructure.orm import ObservationORM  # noqa: F401
from app.shared.infrastructure.database import Base, get_db_session
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ─── Domain unit tests ────────────────────────────────────────────────────────


def test_observation_invariants() -> None:
    now = datetime.now(UTC)
    obs = Observation(
        entity_id="urn:ngsi-v2:Sensor:1",
        attribute_name="pm25",
        timestamp=now,
        value_numeric=42.5,
        unit="ug/m3",
    )
    assert obs.entity_id == "urn:ngsi-v2:Sensor:1"
    assert obs.value_numeric == 42.5

    with pytest.raises(ValueError):
        Observation(entity_id="", attribute_name="pm25", timestamp=now, value_numeric=1.0)

    with pytest.raises(ValueError):
        Observation(entity_id="urn:ngsi-v2:Sensor:1", attribute_name="pm25", timestamp=now)


# ─── Integration tests ────────────────────────────────────────────────────────


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
async def test_ingest_single_observation(client: AsyncClient) -> None:
    payload = {
        "entity_id": "urn:ngsi-v2:AirQualityObserved:TestObs-1",
        "attribute_name": "pm25",
        "value_numeric": 35.5,
        "unit": "ug/m3",
    }
    resp = await client.post("/v1/observations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["entity_id"] == payload["entity_id"]
    assert data["value_numeric"] == 35.5


@pytest.mark.anyio
async def test_bulk_ingest_and_query_observations(client: AsyncClient) -> None:
    entity_id = "urn:ngsi-v2:TrafficFlowObserved:TestTraffic-1"
    bulk_payload = {
        "observations": [
            {
                "entity_id": entity_id,
                "attribute_name": "vehicleCount",
                "value_numeric": 88.0,
                "unit": "count",
            },
            {
                "entity_id": entity_id,
                "attribute_name": "averageSpeed",
                "value_numeric": 45.2,
                "unit": "km/h",
            },
        ]
    }

    # 1. Bulk Ingest
    resp = await client.post("/v1/observations/bulk", json=bulk_payload)
    assert resp.status_code == 201
    assert len(resp.json()) == 2

    # 2. Query time-series
    resp = await client.get(f"/v1/observations?entity_id={entity_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 3. Query latest
    resp = await client.get(f"/v1/observations/latest?entity_id={entity_id}")
    assert resp.status_code == 200
    latest = resp.json()
    assert len(latest) == 2
    attr_names = {item["attribute_name"] for item in latest}
    assert attr_names == {"vehicleCount", "averageSpeed"}
