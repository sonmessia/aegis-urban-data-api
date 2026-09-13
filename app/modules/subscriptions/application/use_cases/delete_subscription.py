"""Use case: Delete a subscription."""

from app.modules.subscriptions.domain.exceptions import SubscriptionNotFoundError
from app.modules.subscriptions.domain.repository import ISubscriptionRepository
from app.modules.subscriptions.domain.value_objects import SubscriptionId


class DeleteSubscriptionUseCase:
    """Orchestrates removing a subscription."""

    def __init__(self, repository: ISubscriptionRepository) -> None:
        self._repository = repository

    async def execute(self, subscription_id_str: str) -> None:
        sub_id = SubscriptionId(subscription_id_str)
        sub = await self._repository.get_by_id(sub_id)
        if sub is None:
            raise SubscriptionNotFoundError(subscription_id_str)
        await self._repository.delete(sub)
