"""Tests for entities module — domain unit tests and API integration tests."""

import pytest
from app.main import create_app
from app.modules.entities.domain.models import Entity
from app.modules.entities.domain.value_objects import EntityId, EntityType
from app.shared.infrastructure.database import Base, get_db_session
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ─── Domain unit tests (Pure Python, Zero DB) ─────────────────────────────────


def test_value_object_validations() -> None:
    entity_id = EntityId("urn:ngsi-v2:AirQualityObserved:001")
    assert str(entity_id) == "urn:ngsi-v2:AirQualityObserved:001"

    entity_type = EntityType("AirQualityObserved")
    assert str(entity_type) == "AirQualityObserved"

    with pytest.raises(ValueError):
        EntityId("")

    with pytest.raises(ValueError):
        EntityType("x" * 129)


def test_domain_entity_update_attributes() -> None:
    entity = Entity(
        entity_id=EntityId("urn:ngsi-v2:Sensor:1"),
        entity_type=EntityType("Sensor"),
        attributes={"temp": {"value": 20}},
    )
    old_updated_at = entity.updated_at
    entity.update_attributes({"humidity": {"value": 50}})

    assert entity.attributes["temp"] == {"value": 20}
    assert entity.attributes["humidity"] == {"value": 50}
    assert entity.updated_at >= old_updated_at


# ─── Integration tests with in-memory SQLite ──────────────────────────────────


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    """In-memory SQLite for fast tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Provide a transactional session that rolls back after each test."""
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """FastAPI test client with DB session override."""

    async def override_get_db_session():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ─── Health endpoints ─────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ─── Entity CRUD ──────────────────────────────────────────────────────────────

ENTITY_PAYLOAD = {
    "id": "urn:ngsi-v2:AirQualityObserved:Test-001",
    "type": "AirQualityObserved",
    "attributes": {
        "pm25": {"value": 42.5, "type": "Number"},
        "temperature": {"value": 31.2, "type": "Number"},
    },
}


@pytest.mark.anyio
async def test_create_entity(client: AsyncClient) -> None:
    response = await client.post("/v1/entities", json=ENTITY_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["entity_id"] == ENTITY_PAYLOAD["id"]
    assert data["entity_type"] == ENTITY_PAYLOAD["type"]


@pytest.mark.anyio
async def test_create_entity_duplicate_returns_409(client: AsyncClient) -> None:
    await client.post("/v1/entities", json=ENTITY_PAYLOAD)
    response = await client.post("/v1/entities", json=ENTITY_PAYLOAD)
    assert response.status_code == 409


@pytest.mark.anyio
async def test_get_entity(client: AsyncClient) -> None:
    await client.post("/v1/entities", json=ENTITY_PAYLOAD)
    entity_id = ENTITY_PAYLOAD["id"]
    response = await client.get(f"/v1/entities/{entity_id}")
    assert response.status_code == 200
    assert response.json()["entity_id"] == entity_id


@pytest.mark.anyio
async def test_get_entity_not_found(client: AsyncClient) -> None:
    response = await client.get("/v1/entities/urn:ngsi-v2:Unknown:999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_entities(client: AsyncClient) -> None:
    await client.post("/v1/entities", json=ENTITY_PAYLOAD)
    response = await client.get("/v1/entities")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_update_entity(client: AsyncClient) -> None:
    await client.post("/v1/entities", json=ENTITY_PAYLOAD)
    entity_id = ENTITY_PAYLOAD["id"]
    patch = {"attributes": {"pm25": {"value": 99.9, "type": "Number"}}}
    response = await client.patch(f"/v1/entities/{entity_id}", json=patch)
    assert response.status_code == 200
    attrs = response.json()["attributes"]
    assert attrs["pm25"]["value"] == 99.9
    # Unlisted attributes preserved
    assert "temperature" in attrs


@pytest.mark.anyio
async def test_delete_entity(client: AsyncClient) -> None:
    await client.post("/v1/entities", json=ENTITY_PAYLOAD)
    entity_id = ENTITY_PAYLOAD["id"]
    response = await client.delete(f"/v1/entities/{entity_id}")
    assert response.status_code == 204
    # Confirm gone
    response = await client.get(f"/v1/entities/{entity_id}")
    assert response.status_code == 404
