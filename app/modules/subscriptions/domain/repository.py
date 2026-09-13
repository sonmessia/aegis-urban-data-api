"""Domain repository interface for Subscriptions."""

from abc import ABC, abstractmethod

from app.modules.subscriptions.domain.models import Subscription
from app.modules.subscriptions.domain.value_objects import (
    SubscriptionId,
    SubscriptionStatus,
)


class ISubscriptionRepository(ABC):
    """Abstract repository for Subscriptions."""

    @abstractmethod
    async def add(self, subscription: Subscription) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, subscription_id: SubscriptionId) -> Subscription | None:
        raise NotImplementedError

    @abstractmethod
    async def list_subscriptions(
        self,
        status: SubscriptionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Subscription], int]:
        raise NotImplementedError

    @abstractmethod
    async def find_active_by_entity_type(self, entity_type: str) -> list[Subscription]:
        """Query all active subscriptions listening to the given entity type."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, subscription: Subscription) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, subscription: Subscription) -> None:
        raise NotImplementedError
