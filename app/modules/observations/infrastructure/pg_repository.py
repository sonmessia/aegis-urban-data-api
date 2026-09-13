"""Postgres implementation of IObservationRepository."""

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.observations.domain.models import Observation
from app.modules.observations.domain.repository import IObservationRepository
from app.modules.observations.infrastructure.orm import ObservationORM


class PostgresObservationRepository(IObservationRepository):
    """Observation repository using SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: ObservationORM) -> Observation:
        return Observation(
            id=orm.id,
            entity_id=orm.entity_id,
            attribute_name=orm.attribute_name,
            timestamp=orm.timestamp,
            value_numeric=orm.value_numeric,
            value_text=orm.value_text,
            unit=orm.unit,
            created_at=orm.created_at,
        )

    async def add_bulk(self, observations: list[Observation]) -> None:
        if not observations:
            return

        orms = [
            ObservationORM(
                id=obs.id,
                entity_id=obs.entity_id,
                attribute_name=obs.attribute_name,
                timestamp=obs.timestamp,
                value_numeric=obs.value_numeric,
                value_text=obs.value_text,
                unit=obs.unit,
                created_at=obs.created_at,
            )
            for obs in observations
        ]
        self._session.add_all(orms)
        await self._session.flush()

    async def query(
        self,
        entity_id: str,
        attribute_name: str | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Observation], int]:
        q = select(ObservationORM).where(ObservationORM.entity_id == entity_id)

        if attribute_name:
            q = q.where(ObservationORM.attribute_name == attribute_name)
        if from_time:
            q = q.where(ObservationORM.timestamp >= from_time)
        if to_time:
            q = q.where(ObservationORM.timestamp <= to_time)

        total_stmt = select(func.count()).select_from(q.subquery())
        total = await self._session.scalar(total_stmt) or 0

        orms = await self._session.scalars(
            q.order_by(desc(ObservationORM.timestamp)).offset(offset).limit(limit)
        )
        return [self._to_domain(orm) for orm in orms], total

    async def get_latest(self, entity_id: str) -> list[Observation]:
        """Fetch the most recent observation for each attribute of an entity."""
        # Query distinct attribute names for this entity
        attrs_stmt = (
            select(ObservationORM.attribute_name)
            .where(ObservationORM.entity_id == entity_id)
            .distinct()
        )
        attribute_names = await self._session.scalars(attrs_stmt)

        results: list[Observation] = []
        for attr in attribute_names:
            latest_stmt = (
                select(ObservationORM)
                .where(
                    ObservationORM.entity_id == entity_id,
                    ObservationORM.attribute_name == attr,
                )
                .order_by(desc(ObservationORM.timestamp))
                .limit(1)
            )
            orm = await self._session.scalar(latest_stmt)
            if orm:
                results.append(self._to_domain(orm))

        return results
