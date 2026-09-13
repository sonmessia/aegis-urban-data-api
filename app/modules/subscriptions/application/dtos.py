"""Application layer DTOs for Subscriptions module."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.modules.subscriptions.domain.models import Subscription


@dataclass(frozen=True)
class SubscriptionDTO:
    id: uuid.UUID
    subscription_id: str
    description: str
    subject_entity_type: str
    subject_entity_id_pattern: str | None
    watched_attributes: list[str]
    notification_url: str
    notification_headers: dict[str, str]
    status: str
    notification_count: int
    last_notification: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, sub: Subscription) -> "SubscriptionDTO":
        return cls(
            id=sub.id,
            subscription_id=str(sub.subscription_id),
            description=sub.description,
            subject_entity_type=sub.subject_entity_type,
            subject_entity_id_pattern=sub.subject_entity_id_pattern,
            watched_attributes=sub.watched_attributes,
            notification_url=sub.notification_endpoint.url,
            notification_headers=sub.notification_endpoint.headers,
            status=sub.status.value,
            notification_count=sub.notification_count,
            last_notification=sub.last_notification,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )


@dataclass(frozen=True)
class CreateSubscriptionCommand:
    subscription_id: str
    description: str
    subject_entity_type: str
    notification_url: str
    notification_headers: dict[str, str]
    subject_entity_id_pattern: str | None = None
    watched_attributes: list[str] | None = None


@dataclass(frozen=True)
class SubscriptionListDTO:
    items: list[SubscriptionDTO]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class EntityChangedEvent:
    """Event emitted when an entity is created or updated."""

    entity_id: str
    entity_type: str
    attributes: dict[str, Any]
    changed_attribute_names: list[str]
