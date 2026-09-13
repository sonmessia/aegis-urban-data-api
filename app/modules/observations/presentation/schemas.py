"""Pydantic v2 schemas for Observations telemetry API."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.observations.application.dtos import (
    IngestObservationItem,
    ObservationDTO,
    ObservationListDTO,
)


class ObservationIn(BaseModel):
    entity_id: str = Field(..., min_length=1, max_length=256)
    attribute_name: str = Field(..., min_length=1, max_length=128)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None

    def to_item(self) -> IngestObservationItem:
        return IngestObservationItem(
            entity_id=self.entity_id,
            attribute_name=self.attribute_name,
            timestamp=self.timestamp,
            value_numeric=self.value_numeric,
            value_text=self.value_text,
            unit=self.unit,
        )


class ObservationBulkIn(BaseModel):
    """Bulk ingestion payload for high-frequency IoT gateways."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "observations": [
                    {
                        "entity_id": "urn:ngsi-v2:AirQualityObserved:HCM-District1-001",
                        "attribute_name": "pm25",
                        "value_numeric": 42.5,
                        "unit": "ug/m3",
                    },
                    {
                        "entity_id": "urn:ngsi-v2:AirQualityObserved:HCM-District1-001",
                        "attribute_name": "temperature",
                        "value_numeric": 31.5,
                        "unit": "CEL",
                    },
                ]
            }
        }
    )

    observations: list[ObservationIn] = Field(..., min_length=1, max_length=1000)


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: str
    attribute_name: str
    timestamp: datetime
    value_numeric: float | None
    value_text: str | None
    unit: str | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: ObservationDTO) -> "ObservationResponse":
        return cls(
            id=dto.id,
            entity_id=dto.entity_id,
            attribute_name=dto.attribute_name,
            timestamp=dto.timestamp,
            value_numeric=dto.value_numeric,
            value_text=dto.value_text,
            unit=dto.unit,
            created_at=dto.created_at,
        )


class ObservationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ObservationResponse]

    @classmethod
    def from_dto(cls, dto: ObservationListDTO) -> "ObservationListResponse":
        return cls(
            total=dto.total,
            page=dto.page,
            page_size=dto.page_size,
            items=[ObservationResponse.from_dto(item) for item in dto.items],
        )
