"""Pydantic v2 presentation schemas for FIWARE NGSI-v2 API."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.entities.application.dtos import (
    CreateEntityCommand,
    EntityDTO,
    EntityListDTO,
    UpdateEntityCommand,
)


class AttributeValue(BaseModel):
    """Single NGSI-v2 attribute with value and optional metadata."""

    model_config = ConfigDict(extra="allow")

    value: Any = Field(..., description="Attribute value (any JSON-serialisable type)")
    type: str = Field(default="Text", description="NGSI-v2 attribute type")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Attribute metadata (e.g., unit, timestamp)",
    )


class EntityCreateRequest(BaseModel):
    """Request body for POST /v1/entities."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "urn:ngsi-v2:AirQualityObserved:HCM-District1-001",
                "type": "AirQualityObserved",
                "attributes": {
                    "pm25": {
                        "value": 42.5,
                        "type": "Number",
                        "metadata": {"unitCode": {"value": "GQ"}},
                    },
                    "temperature": {"value": 31.2, "type": "Number"},
                    "location": {
                        "value": {"type": "Point", "coordinates": [106.6956, 10.7769]},
                        "type": "geo:json",
                    },
                },
            }
        }
    )

    id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="FIWARE entity ID (e.g., 'urn:ngsi-v2:Sensor:001')",
    )
    type: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="FIWARE entity type",
    )
    attributes: dict[str, AttributeValue] = Field(
        default_factory=dict,
        description="NGSI-v2 attributes keyed by attribute name",
    )

    def to_command(self) -> CreateEntityCommand:
        return CreateEntityCommand(
            entity_id=self.id,
            entity_type=self.type,
            attributes={k: v.model_dump() for k, v in self.attributes.items()},
        )


class EntityUpdateRequest(BaseModel):
    """Request body for PATCH /v1/entities/{id}."""

    attributes: dict[str, AttributeValue] = Field(
        ...,
        min_length=1,
        description="Attributes to upsert",
    )

    def to_command(self, entity_id: str) -> UpdateEntityCommand:
        return UpdateEntityCommand(
            entity_id=entity_id,
            attributes={k: v.model_dump() for k, v in self.attributes.items()},
        )


class EntityResponse(BaseModel):
    """Full entity representation returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: str
    entity_type: str
    attributes: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dto(cls, dto: EntityDTO) -> "EntityResponse":
        return cls(
            id=dto.id,
            entity_id=dto.entity_id,
            entity_type=dto.entity_type,
            attributes=dto.attributes,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class EntityListResponse(BaseModel):
    """Paginated list response."""

    total: int
    page: int
    page_size: int
    items: list[EntityResponse]

    @classmethod
    def from_dto(cls, dto: EntityListDTO) -> "EntityListResponse":
        return cls(
            total=dto.total,
            page=dto.page,
            page_size=dto.page_size,
            items=[EntityResponse.from_dto(item) for item in dto.items],
        )
