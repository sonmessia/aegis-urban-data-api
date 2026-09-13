"""Postgres implementation of ISubscriptionRepository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.subscriptions.domain.models import Subscription
from app.modules.subscriptions.domain.repository import ISubscriptionRepository
from app.modules.subscriptions.domain.value_objects import (
    NotificationEndpoint,
    SubscriptionId,
    SubscriptionStatus,
)
from app.modules.subscriptions.infrastructure.orm import SubscriptionORM


class PostgresSubscriptionRepository(ISubscriptionRepository):
    """Subscription repository using SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: SubscriptionORM) -> Subscription:
        return Subscription(
            id=orm.id,
            subscription_id=SubscriptionId(orm.subscription_id),
            description=orm.description,
            subject_entity_type=orm.subject_entity_type,
            subject_entity_id_pattern=orm.subject_entity_id_pattern,
            watched_attributes=orm.watched_attributes,
            notification_endpoint=NotificationEndpoint(
                url=orm.notification_url,
                headers=orm.notification_headers,
            ),
            status=SubscriptionStatus(orm.status),
            notification_count=orm.notification_count,
            last_notification=orm.last_notification,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    async def add(self, subscription: Subscription) -> None:
        orm = SubscriptionORM(
            id=subscription.id,
            subscription_id=str(subscription.subscription_id),
            description=subscription.description,
            subject_entity_type=subscription.subject_entity_type,
            subject_entity_id_pattern=subscription.subject_entity_id_pattern,
            watched_attributes=subscription.watched_attributes,
            notification_url=subscription.notification_endpoint.url,
            notification_headers=subscription.notification_endpoint.headers,
            status=subscription.status.value,
            notification_count=subscription.notification_count,
            last_notification=subscription.last_notification,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm)
        subscription.id = orm.id
        subscription.created_at = orm.created_at
        subscription.updated_at = orm.updated_at

    async def get_by_id(self, subscription_id: SubscriptionId) -> Subscription | None:
        stmt = select(SubscriptionORM).where(
            SubscriptionORM.subscription_id == str(subscription_id)
        )
        orm = await self._session.scalar(stmt)
        if orm is None:
            return None
        return self._to_domain(orm)

    async def list_subscriptions(
        self,
        status: SubscriptionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Subscription], int]:
        query = select(SubscriptionORM)
        if status is not None:
            query = query.where(SubscriptionORM.status == status.value)

        total_stmt = select(func.count()).select_from(query.subquery())
        total = await self._session.scalar(total_stmt) or 0

        orms = await self._session.scalars(query.offset(offset).limit(limit))
        return [self._to_domain(orm) for orm in orms], total

    async def find_active_by_entity_type(self, entity_type: str) -> list[Subscription]:
        stmt = select(SubscriptionORM).where(
            SubscriptionORM.subject_entity_type == entity_type,
            SubscriptionORM.status == SubscriptionStatus.ACTIVE.value,
        )
        orms = await self._session.scalars(stmt)
        return [self._to_domain(orm) for orm in orms]

    async def update(self, subscription: Subscription) -> None:
        stmt = select(SubscriptionORM).where(
            SubscriptionORM.subscription_id == str(subscription.subscription_id)
        )
        orm = await self._session.scalar(stmt)
        if orm is not None:
            orm.status = subscription.status.value
            orm.notification_count = subscription.notification_count
            orm.last_notification = subscription.last_notification
            orm.updated_at = subscription.updated_at
            await self._session.flush()

    async def delete(self, subscription: Subscription) -> None:
        stmt = select(SubscriptionORM).where(
            SubscriptionORM.subscription_id == str(subscription.subscription_id)
        )
        orm = await self._session.scalar(stmt)
        if orm is not None:
            await self._session.delete(orm)
            await self._session.flush()
