"""Pydantic v2 schemas for FIWARE NGSI-v2 entity API."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ─── Attribute schemas ────────────────────────────────────────────────────────

class AttributeValue(BaseModel):
    """Single NGSI-v2 attribute with value and optional metadata."""

    model_config = ConfigDict(extra="allow")  # allow arbitrary metadata fields

    value: Any = Field(..., description="Attribute value (any JSON-serialisable type)")
    type: str = Field(default="Text", description="NGSI-v2 attribute type")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Attribute metadata (e.g., unit, timestamp)",
    )


# ─── Request schemas ──────────────────────────────────────────────────────────

class EntityCreate(BaseModel):
    """Request body for POST /v1/entities — ingest a new IoT entity."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "urn:ngsi-v2:AirQualityObserved:HCM-District1-001",
                "type": "AirQualityObserved",
                "attributes": {
                    "pm25": {"value": 42.5, "type": "Number", "metadata": {"unitCode": {"value": "GQ"}}},
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


class EntityUpdate(BaseModel):
    """Request body for PATCH /v1/entities/{id} — partial attribute update."""

    attributes: dict[str, AttributeValue] = Field(
        ...,
        min_length=1,
        description="Attributes to upsert (existing attributes not listed are preserved)",
    )


# ─── Response schemas ─────────────────────────────────────────────────────────

class EntityResponse(BaseModel):
    """Full entity representation returned by GET / POST."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: str
    entity_type: str
    attributes: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EntityListResponse(BaseModel):
    """Paginated list of entities."""

    total: int
    page: int
    page_size: int
    items: list[EntityResponse]
