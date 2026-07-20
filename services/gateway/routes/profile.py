from __future__ import annotations

import uuid

from fastapi import APIRouter

from services.database import get_session_ctx
from services.gateway.schemas.profile import (
    GardenPlant,
    GardenResponse,
    InterestItem,
    MemoryItem,
    ProfileResponse,
    SnapshotItem,
)
from services.profile.repository import ChildRepo, ProfileRepo

router = APIRouter(prefix="/children", tags=["profile"])

PLANT_COLORS = {
    "恐龙": "#4CAF50", "太空": "#9C27B0", "海洋": "#2196F3",
    "动物": "#FF9800", "植物": "#8BC34A", "科学": "#00BCD4",
    "绘画": "#E91E63", "音乐": "#673AB7", "运动": "#F44336",
    "数学": "#607D8B",
}


def _plant_stage(weight: float) -> str:
    if weight < 0.3:
        return "seed"
    if weight < 0.5:
        return "sprout"
    if weight < 0.8:
        return "growing"
    return "blooming"


def _garden_level(snapshot_avg: float, interest_count: int, memory_count: int) -> int:
    score = snapshot_avg * 0.4 + min(interest_count / 5, 1.0) * 0.3 + min(memory_count / 10, 1.0) * 0.3
    if score < 0.2:
        return 1
    if score < 0.4:
        return 2
    if score < 0.6:
        return 3
    if score < 0.8:
        return 4
    return 5


@router.get("/{child_id}/profile", response_model=ProfileResponse)
async def get_profile(child_id: str) -> ProfileResponse:
    child_uuid = uuid.UUID(child_id)
    child_uuid_hex = child_uuid.hex

    async with get_session_ctx() as session:
        child_repo = ChildRepo(session)
        child = await child_repo.get(child_uuid)
        if not child:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Child not found")

        profile_repo = ProfileRepo(session)
        snapshot = await profile_repo.get_latest_snapshot(child_uuid)

        snapshot_item = None
        if snapshot:
            snapshot_item = SnapshotItem(
                recorded_at=snapshot.recorded_at.isoformat() if snapshot.recorded_at else "",
                vocabulary_level=snapshot.vocabulary_level.value,
                curiosity_score=snapshot.curiosity_score,
                expression_score=snapshot.expression_score,
                reading_score=snapshot.reading_score,
                thinking_score=snapshot.thinking_score,
                learning_style=snapshot.learning_style.value,
                emotion_trend=snapshot.emotion_trend,
            )

        interests = await profile_repo.get_interests(child_uuid)
        interest_items = [
            InterestItem(topic=i.topic, weight=i.weight, trend=i.trend.value)
            for i in interests
        ]

        # Recent memories via raw SQL (UUID format differs in long_memories)
        from sqlalchemy import text
        uuid_dash = str(child_uuid)
        mem_result = await session.execute(
            text("SELECT memory_type, importance, content, created_at FROM long_memories "
                 "WHERE child_id=:cid ORDER BY created_at DESC LIMIT 5"),
            {"cid": uuid_dash},
        )
        memories = [
            MemoryItem(
                memory_type=row._mapping["memory_type"],
                importance=row._mapping["importance"],
                content=row._mapping["content"],
                created_at=row._mapping["created_at"],
            )
            for row in mem_result.fetchall()
        ]

        return ProfileResponse(
            child_id=str(child.id),
            nickname=child.nickname,
            age=child.age,
            grade=child.grade,
            snapshot=snapshot_item,
            interests=interest_items,
            recent_memories=memories,
        )


@router.get("/{child_id}/garden", response_model=GardenResponse)
async def get_garden(child_id: str) -> GardenResponse:
    child_uuid = uuid.UUID(child_id)

    async with get_session_ctx() as session:
        child_repo = ChildRepo(session)
        child = await child_repo.get(child_uuid)
        if not child:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Child not found")

        profile_repo = ProfileRepo(session)
        snapshot = await profile_repo.get_latest_snapshot(child_uuid)
        interests = await profile_repo.get_interests(child_uuid)

        from sqlalchemy import text
        mem_count = await session.execute(
            text("SELECT count(*) as c FROM long_memories WHERE child_id=:cid"),
            {"cid": str(child_uuid)},
        )
        total_memories = mem_count.first()._mapping["c"]

        plants = [
            GardenPlant(
                topic=i.topic,
                weight=i.weight,
                trend=i.trend.value,
                stage=_plant_stage(i.weight),
                color=PLANT_COLORS.get(i.topic, "#9E9E9E"),
            )
            for i in interests
        ]

        soil_quality = 0.5
        if snapshot:
            soil_quality = (
                snapshot.curiosity_score + snapshot.expression_score +
                snapshot.reading_score + snapshot.thinking_score
            ) / 4.0

        garden_level = _garden_level(soil_quality, len(interests), total_memories)

        return GardenResponse(
            child_id=str(child.id),
            nickname=child.nickname,
            plants=plants,
            soil_quality=round(soil_quality, 2),
            garden_level=garden_level,
            total_memories=total_memories,
        )
