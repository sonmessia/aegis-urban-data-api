"""Tests for Subscriptions module — domain unit tests and API integration tests."""

import pytest
from app.main import create_app
from app.modules.subscriptions.domain.models import Subscription
from app.modules.subscriptions.domain.value_objects import (
    NotificationEndpoint,
    SubscriptionId,
    SubscriptionStatus,
)
from app.modules.subscriptions.infrastructure.orm import SubscriptionORM  # noqa: F401
from app.shared.infrastructure.database import Base, get_db_session
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ─── Domain unit tests ────────────────────────────────────────────────────────


def test_subscription_value_objects() -> None:
    sub_id = SubscriptionId("sub:urban:air-alerts")
    assert str(sub_id) == "sub:urban:air-alerts"

    with pytest.raises(ValueError):
        SubscriptionId("")

    endpoint = NotificationEndpoint(url="http://example.com/webhook", headers={"X-Key": "val"})
    assert endpoint.url == "http://example.com/webhook"

    with pytest.raises(ValueError):
        NotificationEndpoint(url="ftp://invalid.com", headers={})


def test_subscription_matching_logic() -> None:
    sub = Subscription(
        subscription_id=SubscriptionId("sub:d1:air"),
        description="Air alerts for District 1",
        subject_entity_type="AirQualityObserved",
        subject_entity_id_pattern="urn:ngsi-v2:AirQualityObserved:D1-*",
        watched_attributes=["pm25", "co2"],
        notification_endpoint=NotificationEndpoint(url="http://alert.local/hook", headers={}),
    )

    # Matching entity type, id pattern, and watched attribute
    assert sub.matches(
        entity_type="AirQualityObserved",
        entity_id="urn:ngsi-v2:AirQualityObserved:D1-001",
        changed_attrs=["pm25"],
    )

    # Non-matching entity type
    assert not sub.matches(
        entity_type="TrafficFlowObserved",
        entity_id="urn:ngsi-v2:AirQualityObserved:D1-001",
        changed_attrs=["pm25"],
    )

    # Non-matching ID pattern
    assert not sub.matches(
        entity_type="AirQualityObserved",
        entity_id="urn:ngsi-v2:AirQualityObserved:D7-001",
        changed_attrs=["pm25"],
    )

    # Non-matching attribute
    assert not sub.matches(
        entity_type="AirQualityObserved",
        entity_id="urn:ngsi-v2:AirQualityObserved:D1-001",
        changed_attrs=["humidity"],
    )


# ─── API Integration tests ────────────────────────────────────────────────────


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


SUB_PAYLOAD = {
    "id": "sub:test:air-alerts",
    "description": "Test air quality subscription",
    "subject_type": "AirQualityObserved",
    "subject_id_pattern": "urn:ngsi-v2:AirQualityObserved:*",
    "watched_attributes": ["pm25"],
    "notification": {
        "url": "http://alert-manager.local/webhook",
        "headers": {"X-Custom": "test"},
    },
}


@pytest.mark.anyio
async def test_subscription_crud_lifecycle(client: AsyncClient) -> None:
    # 1. Create
    resp = await client.post("/v1/subscriptions", json=SUB_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["subscription_id"] == SUB_PAYLOAD["id"]
    assert data["status"] == "active"

    # 2. Duplicate returns 409
    dup = await client.post("/v1/subscriptions", json=SUB_PAYLOAD)
    assert dup.status_code == 409

    # 3. Get
    sub_id = SUB_PAYLOAD["id"]
    resp = await client.get(f"/v1/subscriptions/{sub_id}")
    assert resp.status_code == 200
    assert resp.json()["subscription_id"] == sub_id

    # 4. List
    resp = await client.get("/v1/subscriptions")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # 5. Delete
    resp = await client.delete(f"/v1/subscriptions/{sub_id}")
    assert resp.status_code == 204

    # 6. Verify 404 after delete
    resp = await client.get(f"/v1/subscriptions/{sub_id}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_notify_subscribers_orchestration(db_session: AsyncSession) -> None:
    from app.modules.subscriptions.application.dtos import (
        CreateSubscriptionCommand,
        EntityChangedEvent,
    )
    from app.modules.subscriptions.application.use_cases.create_subscription import (
        CreateSubscriptionUseCase,
    )
    from app.modules.subscriptions.application.use_cases.notify_subscribers import (
        IWebhookDispatcher,
        NotifySubscribersUseCase,
    )
    from app.modules.subscriptions.infrastructure.pg_repository import (
        PostgresSubscriptionRepository,
    )

    class MockDispatcher(IWebhookDispatcher):
        def __init__(self) -> None:
            self.dispatched: list[dict] = []

        async def dispatch(self, subscription: Subscription, payload: dict) -> bool:
            self.dispatched.append(payload)
            return True

    repo = PostgresSubscriptionRepository(db_session)
    dispatcher = MockDispatcher()
    create_uc = CreateSubscriptionUseCase(repo)
    notify_uc = NotifySubscribersUseCase(repo, dispatcher)

    # Create active subscription
    cmd = CreateSubscriptionCommand(
        subscription_id="sub:notify:test",
        description="Notify test",
        subject_entity_type="AirQualityObserved",
        notification_url="http://mock.local/webhook",
        notification_headers={},
        watched_attributes=["pm25"],
    )
    await create_uc.execute(cmd)

    # Event with watched attribute -> should trigger
    event = EntityChangedEvent(
        entity_id="urn:ngsi-v2:AirQualityObserved:Station1",
        entity_type="AirQualityObserved",
        attributes={"pm25": {"value": 55.0}},
        changed_attribute_names=["pm25"],
    )
    count = await notify_uc.execute(event)
    assert count == 1
    assert len(dispatcher.dispatched) == 1

    # Event with unwatched attribute -> should NOT trigger
    event2 = EntityChangedEvent(
        entity_id="urn:ngsi-v2:AirQualityObserved:Station1",
        entity_type="AirQualityObserved",
        attributes={"temperature": {"value": 30.0}},
        changed_attribute_names=["temperature"],
    )
    count2 = await notify_uc.execute(event2)
    assert count2 == 0


def test_subscription_pause_resume() -> None:
    sub = Subscription(
        subscription_id=SubscriptionId("sub:state:test"),
        description="State test",
        subject_entity_type="AirQualityObserved",
        notification_endpoint=NotificationEndpoint(url="http://test.local", headers={}),
    )
    assert sub.status == SubscriptionStatus.ACTIVE
    sub.pause()
    assert sub.status == SubscriptionStatus.PAUSED
    assert not sub.matches("AirQualityObserved", "test", ["pm25"])
    sub.resume()
    assert sub.status == SubscriptionStatus.ACTIVE
