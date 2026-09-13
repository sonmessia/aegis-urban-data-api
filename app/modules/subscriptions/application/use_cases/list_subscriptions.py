"""Use case: List subscriptions with pagination and optional status filter."""

from app.modules.subscriptions.application.dtos import (
    SubscriptionDTO,
    SubscriptionListDTO,
)
from app.modules.subscriptions.domain.repository import ISubscriptionRepository
from app.modules.subscriptions.domain.value_objects import SubscriptionStatus


class ListSubscriptionsUseCase:
    """Orchestrates querying subscriptions."""

    def __init__(self, repository: ISubscriptionRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        status_str: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SubscriptionListDTO:
        status = SubscriptionStatus(status_str) if status_str else None
        offset = (page - 1) * page_size

        subs, total = await self._repository.list_subscriptions(
            status=status,
            limit=page_size,
            offset=offset,
        )

        return SubscriptionListDTO(
            items=[SubscriptionDTO.from_domain(s) for s in subs],
            total=total,
            page=page,
            page_size=page_size,
        )
