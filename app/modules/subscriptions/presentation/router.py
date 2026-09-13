"""FastAPI router for Subscriptions endpoints."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

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
from app.modules.subscriptions.domain.exceptions import (
    SubscriptionAlreadyExistsError,
    SubscriptionNotFoundError,
)
from app.modules.subscriptions.presentation.dependencies import (
    get_create_subscription_use_case,
    get_delete_subscription_use_case,
    get_get_subscription_use_case,
    get_list_subscriptions_use_case,
)
from app.modules.subscriptions.presentation.schemas import (
    SubscriptionCreateRequest,
    SubscriptionListResponse,
    SubscriptionResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "",
    summary="Create subscription",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    payload: SubscriptionCreateRequest,
    use_case: CreateSubscriptionUseCase = Depends(get_create_subscription_use_case),
) -> SubscriptionResponse:
    """Register a new subscription to receive webhooks on entity changes."""
    try:
        dto = await use_case.execute(payload.to_command())
        return SubscriptionResponse.from_dto(dto)
    except SubscriptionAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    summary="List subscriptions",
    response_model=SubscriptionListResponse,
)
async def list_subscriptions(
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by status (active/paused)"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    use_case: ListSubscriptionsUseCase = Depends(get_list_subscriptions_use_case),
) -> SubscriptionListResponse:
    dto = await use_case.execute(status_str=status_filter, page=page, page_size=page_size)
    return SubscriptionListResponse.from_dto(dto)


@router.get(
    "/{subscription_id:path}",
    summary="Get subscription by ID",
    response_model=SubscriptionResponse,
)
async def get_subscription(
    subscription_id: str,
    use_case: GetSubscriptionUseCase = Depends(get_get_subscription_use_case),
) -> SubscriptionResponse:
    try:
        dto = await use_case.execute(subscription_id)
        return SubscriptionResponse.from_dto(dto)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{subscription_id:path}",
    summary="Delete subscription",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subscription(
    subscription_id: str,
    use_case: DeleteSubscriptionUseCase = Depends(get_delete_subscription_use_case),
) -> None:
    try:
        await use_case.execute(subscription_id)
    except SubscriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
