from __future__ import annotations

from fastapi import APIRouter

from services.database import get_session_ctx
from services.gateway.schemas.chat import ChildCreateRequest, ChildResponse
from services.memory.profile_engine import ProfileEngine
from services.profile.repository import ChildRepo, ProfileRepo

router = APIRouter(prefix="/children", tags=["children"])


@router.post("", response_model=ChildResponse)
async def create_child(req: ChildCreateRequest) -> ChildResponse:
    async with get_session_ctx() as session:
        repo = ChildRepo(session)
        child = await repo.create(nickname=req.nickname, age=req.age, grade=req.grade)

        # Create initial profile snapshot
        engine = ProfileEngine()
        snapshot = engine.compute_initial_snapshot(child.id)
        profile_repo = ProfileRepo(session)
        await profile_repo.save_snapshot(snapshot)

        await session.commit()
        return ChildResponse(id=str(child.id), nickname=child.nickname, age=child.age, grade=child.grade)
