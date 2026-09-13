"""FastAPI dependencies for Observations module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.observations.application.use_cases.ingest_observations import (
    IngestObservationsUseCase,
)
from app.modules.observations.application.use_cases.query_observations import (
    QueryObservationsUseCase,
)
from app.modules.observations.domain.repository import IObservationRepository
from app.modules.observations.infrastructure.pg_repository import (
    PostgresObservationRepository,
)
from app.shared.infrastructure.database import get_db_session


def get_observation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IObservationRepository:
    return PostgresObservationRepository(session)


def get_ingest_observations_use_case(
    repo: IObservationRepository = Depends(get_observation_repository),
) -> IngestObservationsUseCase:
    return IngestObservationsUseCase(repo)


def get_query_observations_use_case(
    repo: IObservationRepository = Depends(get_observation_repository),
) -> QueryObservationsUseCase:
    return QueryObservationsUseCase(repo)
