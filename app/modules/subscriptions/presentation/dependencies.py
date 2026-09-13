"""FastAPI dependencies for Subscriptions module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.subscriptions.application.use_cases.create_subscription import (
    CreateSubscriptionUseCase,
)
from app.modules.subscriptions.application.use_cases.delete_subscription import (
    DeleteSubscriptionUseCase,
)
from app.modules.subscriptions.application.use_cases.get_subscription import (
    GetSubscriptionUseCase,
)
from app.modules.subscriptions.application.use_cases.list_subscriptions import (
    ListSubscriptionsUseCase,
)
from app.modules.subscriptions.application.use_cases.notify_subscribers import (
    IWebhookDispatcher,
    NotifySubscribersUseCase,
)
from app.modules.subscriptions.domain.repository import ISubscriptionRepository
from app.modules.subscriptions.infrastructure.pg_repository import (
    PostgresSubscriptionRepository,
)
from app.modules.subscriptions.infrastructure.webhook_dispatcher import (
    HttpWebhookDispatcher,
)
from app.shared.infrastructure.database import get_db_session


def get_subscription_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ISubscriptionRepository:
    return PostgresSubscriptionRepository(session)


def get_webhook_dispatcher() -> IWebhookDispatcher:
    return HttpWebhookDispatcher()


def get_create_subscription_use_case(
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
) -> CreateSubscriptionUseCase:
    return CreateSubscriptionUseCase(repo)


def get_get_subscription_use_case(
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
) -> GetSubscriptionUseCase:
    return GetSubscriptionUseCase(repo)


def get_list_subscriptions_use_case(
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
) -> ListSubscriptionsUseCase:
    return ListSubscriptionsUseCase(repo)


def get_delete_subscription_use_case(
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
) -> DeleteSubscriptionUseCase:
    return DeleteSubscriptionUseCase(repo)


def get_notify_subscribers_use_case(
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
    dispatcher: IWebhookDispatcher = Depends(get_webhook_dispatcher),
) -> NotifySubscribersUseCase:
    return NotifySubscribersUseCase(repo, dispatcher)
