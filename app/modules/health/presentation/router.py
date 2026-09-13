"""FastAPI router for Health and Readiness observability probes."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.database import get_db_session

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["observability"])


@router.get(
    "/health",
    summary="Liveness probe",
    response_model=dict[str, str],
)
async def health() -> dict[str, str]:
    """Liveness probe — returns 200 if the process is running."""
    return {"status": "ok"}


@router.get(
    "/ready",
    summary="Readiness probe",
    response_model=dict[str, str],
)
async def ready(db: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    """
    Readiness probe — verifies database connectivity.
    Returns 503 if the database is unreachable.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "db": "ok"}
    except Exception as exc:
        logger.warning("readiness check failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "db": "unreachable"},
        ) from exc
