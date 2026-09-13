"""Use case: Create a new subscription."""

from app.modules.subscriptions.application.dtos import (
    CreateSubscriptionCommand,
    SubscriptionDTO,
)
from app.modules.subscriptions.domain.exceptions import SubscriptionAlreadyExistsError
from app.modules.subscriptions.domain.models import Subscription
from app.modules.subscriptions.domain.repository import ISubscriptionRepository
from app.modules.subscriptions.domain.value_objects import (
    NotificationEndpoint,
    SubscriptionId,
)


class CreateSubscriptionUseCase:
    """Orchestrates registering a new subscription."""

    def __init__(self, repository: ISubscriptionRepository) -> None:
        self._repository = repository

    async def execute(self, command: CreateSubscriptionCommand) -> SubscriptionDTO:
        sub_id = SubscriptionId(command.subscription_id)

        existing = await self._repository.get_by_id(sub_id)
        if existing is not None:
            raise SubscriptionAlreadyExistsError(command.subscription_id)

        endpoint = NotificationEndpoint(
            url=command.notification_url,
            headers=command.notification_headers,
        )

        subscription = Subscription(
            subscription_id=sub_id,
            description=command.description,
            subject_entity_type=command.subject_entity_type,
            notification_endpoint=endpoint,
            subject_entity_id_pattern=command.subject_entity_id_pattern,
            watched_attributes=command.watched_attributes or [],
        )

        await self._repository.add(subscription)
        return SubscriptionDTO.from_domain(subscription)
