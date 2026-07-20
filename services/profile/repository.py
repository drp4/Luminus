from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.profile.models import Child, InterestModel, Persona, ProfileSnapshot


class ChildRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, nickname: str, age: int, grade: str) -> Child:
        child = Child(nickname=nickname, age=age, grade=grade)
        self._session.add(child)
        await self._session.flush()
        return child

    async def get(self, child_id: uuid.UUID) -> Child | None:
        return await self._session.get(Child, child_id)


class ProfileRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_latest_snapshot(self, child_id: uuid.UUID) -> ProfileSnapshot | None:
        result = await self._session.execute(
            select(ProfileSnapshot)
            .where(ProfileSnapshot.child_id == child_id)
            .order_by(ProfileSnapshot.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save_snapshot(self, snapshot: ProfileSnapshot) -> ProfileSnapshot:
        self._session.add(snapshot)
        await self._session.flush()
        return snapshot

    async def get_interests(self, child_id: uuid.UUID) -> list[InterestModel]:
        result = await self._session.execute(
            select(InterestModel).where(InterestModel.child_id == child_id)
        )
        return list(result.scalars().all())

    async def upsert_interest(self, interest: InterestModel) -> InterestModel:
        existing = await self._session.execute(
            select(InterestModel).where(
                InterestModel.child_id == interest.child_id,
                InterestModel.topic == interest.topic,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.weight = interest.weight
            row.last_seen_at = interest.last_seen_at
            row.trend = interest.trend
            row.source = interest.source
        else:
            self._session.add(interest)
        await self._session.flush()
        return row or interest


class PersonaRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_default(self) -> Persona | None:
        result = await self._session.execute(
            select(Persona).where(Persona.is_default == True).limit(1)
        )
        return result.scalar_one_or_none()

    async def get(self, persona_id: uuid.UUID) -> Persona | None:
        return await self._session.get(Persona, persona_id)
