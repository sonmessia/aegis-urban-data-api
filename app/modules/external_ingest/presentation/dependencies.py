"""FastAPI dependencies for External Ingestion module."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entities.domain.repository import IEntityRepository
from app.modules.entities.infrastructure.pg_repository import (
    PostgresEntityRepository,
)
from app.modules.external_ingest.application.use_cases.sync_public_data import (
    SyncPublicDataUseCase,
)
from app.modules.external_ingest.domain.client_interface import IOpenMeteoClient
from app.modules.external_ingest.infrastructure.open_meteo_client import (
    OpenMeteoClient,
)
from app.modules.observations.domain.repository import IObservationRepository
from app.modules.observations.infrastructure.pg_repository import (
    PostgresObservationRepository,
)
from app.shared.infrastructure.database import get_db_session


def get_open_meteo_client() -> IOpenMeteoClient:
    return OpenMeteoClient()


def get_sync_public_data_use_case(
    client: IOpenMeteoClient = Depends(get_open_meteo_client),
    session: AsyncSession = Depends(get_db_session),
) -> SyncPublicDataUseCase:
    entity_repo: IEntityRepository = PostgresEntityRepository(session)
    observation_repo: IObservationRepository = PostgresObservationRepository(session)
    return SyncPublicDataUseCase(client, entity_repo, observation_repo)
