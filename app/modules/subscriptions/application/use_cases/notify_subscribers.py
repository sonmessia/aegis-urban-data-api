"""Use case: Notify matching subscribers when an entity change occurs."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from app.modules.subscriptions.application.dtos import EntityChangedEvent
from app.modules.subscriptions.domain.models import Subscription
from app.modules.subscriptions.domain.repository import ISubscriptionRepository

logger = structlog.get_logger(__name__)


class IWebhookDispatcher(ABC):
    """Port for delivering HTTP webhook notifications to subscribers."""

    @abstractmethod
    async def dispatch(self, subscription: Subscription, payload: dict[str, Any]) -> bool:
        """Send webhook HTTP POST. Returns True if delivery succeeded, False otherwise."""
        raise NotImplementedError


class NotifySubscribersUseCase:
    """Orchestrates webhook delivery for matching subscriptions."""

    def __init__(
        self,
        repository: ISubscriptionRepository,
        dispatcher: IWebhookDispatcher,
    ) -> None:
        self._repository = repository
        self._dispatcher = dispatcher

    async def execute(self, event: EntityChangedEvent) -> int:
        """
        Evaluate and notify all active subscriptions matching the entity event.
        Returns the count of notifications successfully sent.
        """
        active_subs = await self._repository.find_active_by_entity_type(event.entity_type)
        if not active_subs:
            return 0

        notification_payload: dict[str, Any] = {
            "subscriptionId": None,
            "data": [
                {
                    "id": event.entity_id,
                    "type": event.entity_type,
                    "attributes": event.attributes,
                }
            ],
        }

        notified_count = 0
        for sub in active_subs:
            if sub.matches(
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                changed_attrs=event.changed_attribute_names,
            ):
                notification_payload["subscriptionId"] = str(sub.subscription_id)
                success = await self._dispatcher.dispatch(sub, notification_payload)
                if success:
                    sub.record_notification_success()
                    notified_count += 1
                else:
                    sub.record_notification_failure()

                await self._repository.update(sub)

        logger.info(
            "subscribers notified",
            entity_id=event.entity_id,
            matched=len(active_subs),
            dispatched=notified_count,
        )
        return notified_count
