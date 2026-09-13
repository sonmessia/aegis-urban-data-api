"""Domain aggregate root for Subscriptions."""

import fnmatch
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.subscriptions.domain.value_objects import (
    NotificationEndpoint,
    SubscriptionId,
    SubscriptionStatus,
)


@dataclass
class Subscription:
    """
    FIWARE NGSI-v2 Subscription aggregate root.

    Allows applications to subscribe to entity changes and receive webhook notifications.
    """

    subscription_id: SubscriptionId
    description: str
    subject_entity_type: str
    notification_endpoint: NotificationEndpoint
    subject_entity_id_pattern: str | None = None
    watched_attributes: list[str] = field(default_factory=list)
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    notification_count: int = 0
    last_notification: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def matches(self, entity_type: str, entity_id: str, changed_attrs: list[str]) -> bool:
        """
        Determine if this subscription triggers for an entity change event.
        """
        if self.status != SubscriptionStatus.ACTIVE:
            return False

        # Match entity type
        if self.subject_entity_type != entity_type:
            return False

        # Match entity ID pattern if specified (e.g. 'urn:ngsi-v2:AirQualityObserved:*')
        if self.subject_entity_id_pattern and not fnmatch.fnmatch(
            entity_id, self.subject_entity_id_pattern
        ):
            return False

        # Match watched attributes if specified
        if self.watched_attributes and not any(
            attr in self.watched_attributes for attr in changed_attrs
        ):
            return False

        return True

    def record_notification_success(self) -> None:
        """Record successful delivery of webhook notification."""
        self.notification_count += 1
        self.last_notification = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def record_notification_failure(self) -> None:
        """Record delivery failure."""
        self.updated_at = datetime.now(UTC)

    def pause(self) -> None:
        self.status = SubscriptionStatus.PAUSED
        self.updated_at = datetime.now(UTC)

    def resume(self) -> None:
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.now(UTC)
