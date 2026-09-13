"""HTTP implementation of IWebhookDispatcher using httpx.AsyncClient."""

from typing import Any

import httpx
import structlog

from app.modules.subscriptions.application.use_cases.notify_subscribers import (
    IWebhookDispatcher,
)
from app.modules.subscriptions.domain.models import Subscription

logger = structlog.get_logger(__name__)


class HttpWebhookDispatcher(IWebhookDispatcher):
    """Dispatches webhook notification payloads via HTTP POST."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout = timeout_seconds

    async def dispatch(self, subscription: Subscription, payload: dict[str, Any]) -> bool:
        url = subscription.notification_endpoint.url
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Aegis-UrbanDataAPI-Notification/1.0",
            **subscription.notification_endpoint.headers,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.is_success:
                    logger.info(
                        "webhook delivered",
                        subscription_id=str(subscription.subscription_id),
                        url=url,
                        status_code=response.status_code,
                    )
                    return True
                else:
                    logger.warning(
                        "webhook delivery failed with status",
                        subscription_id=str(subscription.subscription_id),
                        url=url,
                        status_code=response.status_code,
                    )
                    return False
        except Exception as exc:
            logger.warning(
                "webhook delivery exception",
                subscription_id=str(subscription.subscription_id),
                url=url,
                error=str(exc),
            )
            return False
