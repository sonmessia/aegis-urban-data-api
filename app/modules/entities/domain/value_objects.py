"""
Domain layer — Value Objects.

Pure Python dataclasses with no external dependencies.
These enforce invariants at the type level, preventing primitive obsession.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityId:
    """
    FIWARE NGSI-v2 entity identifier.
    Example: 'urn:ngsi-v2:AirQualityObserved:HCM-District1-001'
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) > 256:
            raise ValueError(f"EntityId must be 1-256 characters, got: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EntityType:
    """
    FIWARE NGSI-v2 entity type.
    Example: 'AirQualityObserved', 'WeatherObserved', 'Vehicle'
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) > 128:
            raise ValueError(f"EntityType must be 1-128 characters, got: {self.value!r}")

    def __str__(self) -> str:
        return self.value
