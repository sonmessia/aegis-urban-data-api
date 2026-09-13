"""
Domain layer — Entity aggregate root.

Pure Python dataclass — NO SQLAlchemy, NO FastAPI, NO Pydantic.
This is the heart of the domain: it can be tested without any infrastructure.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.modules.entities.domain.value_objects import EntityId, EntityType


@dataclass
class Entity:
    """
    FIWARE NGSI-v2 Entity aggregate root.

    Attributes stored as a dict of {name: {value, type, metadata}} — matching
    the NGSI-v2 simplified entity representation spec.
    """

    entity_id: EntityId
    entity_type: EntityType
    attributes: dict[str, Any] = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_attributes(self, new_attributes: dict[str, Any]) -> None:
        """
        Merge new attributes over existing ones.
        Attributes not present in new_attributes are preserved (partial update).
        """
        self.attributes = {**self.attributes, **new_attributes}
        self.updated_at = datetime.now(timezone.utc)
