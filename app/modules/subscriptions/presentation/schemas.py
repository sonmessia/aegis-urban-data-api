"""Pydantic v2 schemas for Subscriptions API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.subscriptions.application.dtos import (
    CreateSubscriptionCommand,
    SubscriptionDTO,
    SubscriptionListDTO,
)


class NotificationEndpointSchema(BaseModel):
    url: str = Field(..., description="Webhook callback URL")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Custom HTTP headers to include with webhook"
    )


class SubscriptionCreateRequest(BaseModel):
    """Request body for creating a subscription."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sub:urban:air-quality-alerts",
                "description": "Notify emergency service when air quality changes in District 1",
                "subject": {
                    "entities": [
                        {
                            "idPattern": "urn:ngsi-v2:AirQualityObserved:HCM-District1-.*",
                            "type": "AirQualityObserved",
                        }
                    ],
                    "condition": {
                        "attrs": ["pm25", "co2"],
                    },
                },
                "notification": {
                    "http": {
                        "url": "http://alert-manager.aegis-system.svc.cluster.local:9093/webhook",
                    },
                    "headers": {
                        "X-Alert-Priority": "Critical",
                    },
                },
            }
        }
    )

    id: str = Field(..., min_length=1, max_length=256, description="Subscription business ID")
    description: str = Field(default="", max_length=512)
    subject_type: str = Field(..., description="Entity type to watch")
    subject_id_pattern: str | None = Field(
        default=None, description="Optional entity ID pattern filter"
    )
    watched_attributes: list[str] = Field(
        default_factory=list, description="Attributes that trigger webhook"
    )
    notification: NotificationEndpointSchema

    def to_command(self) -> CreateSubscriptionCommand:
        return CreateSubscriptionCommand(
            subscription_id=self.id,
            description=self.description,
            subject_entity_type=self.subject_type,
            notification_url=self.notification.url,
            notification_headers=self.notification.headers,
            subject_entity_id_pattern=self.subject_id_pattern,
            watched_attributes=self.watched_attributes,
        )


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    def from_dto(cls, dto: SubscriptionDTO) -> "SubscriptionResponse":
        return cls(
            id=dto.id,
            subscription_id=dto.subscription_id,
            description=dto.description,
            subject_entity_type=dto.subject_entity_type,
            subject_entity_id_pattern=dto.subject_entity_id_pattern,
            watched_attributes=dto.watched_attributes,
            notification_url=dto.notification_url,
            notification_headers=dto.notification_headers,
            status=dto.status,
            notification_count=dto.notification_count,
            last_notification=dto.last_notification,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class SubscriptionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SubscriptionResponse]

    @classmethod
    def from_dto(cls, dto: SubscriptionListDTO) -> "SubscriptionListResponse":
        return cls(
            total=dto.total,
            page=dto.page,
            page_size=dto.page_size,
            items=[SubscriptionResponse.from_dto(item) for item in dto.items],
        )
