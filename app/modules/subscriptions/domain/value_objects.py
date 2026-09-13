"""Domain layer — Value Objects for Subscriptions module."""

from dataclasses import dataclass
from enum import StrEnum


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


@dataclass(frozen=True)
class SubscriptionId:
    """Subscription business identifier (e.g. 'sub:urban:air-quality-alerts')."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or len(self.value) > 256:
            raise ValueError(f"SubscriptionId must be 1-256 characters, got: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class NotificationEndpoint:
    """Target destination for webhook notifications."""

    url: str
    headers: dict[str, str]

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(
                f"NotificationEndpoint url must start with http:// or https://, got: {self.url!r}"
            )
