"""Background event dispatcher for entity change notifications."""

from typing import Any

import structlog

from app.modules.subscriptions.application.dtos import EntityChangedEvent
from app.modules.subscriptions.application.use_cases.notify_subscribers import (
    NotifySubscribersUseCase,
)
from app.modules.subscriptions.infrastructure.pg_repository import (
    PostgresSubscriptionRepository,
)
from app.modules.subscriptions.infrastructure.webhook_dispatcher import (
    HttpWebhookDispatcher,
)
from app.shared.infrastructure.database import sessionmanager

logger = structlog.get_logger(__name__)


async def handle_entity_changed(
    entity_id: str,
    entity_type: str,
    attributes: dict[str, Any],
    changed_attributes: list[str],
) -> None:
    """
    Background worker invoked when an entity is created or updated.
    Runs in its own session to safely deliver webhooks and record delivery metrics.
    """
    try:
        async with sessionmanager.session() as session:
            repo = PostgresSubscriptionRepository(session)
            dispatcher = HttpWebhookDispatcher()
            use_case = NotifySubscribersUseCase(repository=repo, dispatcher=dispatcher)

            event = EntityChangedEvent(
                entity_id=entity_id,
                entity_type=entity_type,
                attributes=attributes,
                changed_attribute_names=changed_attributes,
            )
            await use_case.execute(event)
    except Exception as exc:
        logger.error(
            "failed to process entity changed background event",
            entity_id=entity_id,
            error=str(exc),
        )
