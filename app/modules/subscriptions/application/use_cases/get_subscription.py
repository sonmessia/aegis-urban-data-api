"""Use case: Get subscription by ID."""

from app.modules.subscriptions.application.dtos import SubscriptionDTO
from app.modules.subscriptions.domain.exceptions import SubscriptionNotFoundError
from app.modules.subscriptions.domain.repository import ISubscriptionRepository
from app.modules.subscriptions.domain.value_objects import SubscriptionId


class GetSubscriptionUseCase:
    """Orchestrates retrieving a subscription."""

    def __init__(self, repository: ISubscriptionRepository) -> None:
        self._repository = repository

    async def execute(self, subscription_id_str: str) -> SubscriptionDTO:
        sub_id = SubscriptionId(subscription_id_str)
        sub = await self._repository.get_by_id(sub_id)
        if sub is None:
            raise SubscriptionNotFoundError(subscription_id_str)
        return SubscriptionDTO.from_domain(sub)
