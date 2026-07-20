from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from services.database import get_session_ctx
from services.gateway.schemas.chat import ChatRequest, ChatResponse
from services.runtime.kernel import AgentRuntime
from services.memory.store import MemoryStore
from services.memory.profile_engine import ProfileEngine
from services.agent.agents.memory_agent import MemoryAgent
from services.profile.repository import ProfileRepo
from config import settings

router = APIRouter(tags=["chat"])

_runtime: AgentRuntime | None = None


def get_runtime() -> AgentRuntime:
    if _runtime is None:
        raise HTTPException(status_code=503, detail="Runtime not initialized")
    return _runtime


def init_runtime(runtime: AgentRuntime) -> None:
    global _runtime
    _runtime = runtime


async def _run_reflection(child_id: str, messages: list[dict]) -> None:
    """Run Memory Agent Reflection Loop after conversation ends."""
    import logging
    logger = logging.getLogger("reflection")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        import sys
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.INFO)
        logger.addHandler(h)
    try:
        child_uuid = uuid.UUID(child_id)
        logger.info(f"Reflection started for child={child_uuid.hex[:12]}... messages={len(messages)}")
        async with get_session_ctx() as session:
            store = MemoryStore(session, mode=settings.vector_store)
            await store.ensure_table()
            agent = MemoryAgent(store)
            facts = await agent.reflect(str(child_uuid), messages)
            logger.info(f"Reflection: {len(facts)} facts extracted")

            if facts:
                engine = ProfileEngine()
                profile_repo = ProfileRepo(session)

                # Interest facts → interest_models
                interest_models = engine.facts_to_interests(child_uuid, facts)
                for im in interest_models:
                    await profile_repo.upsert_interest(im)
                logger.info(f"Interests saved: {len(interest_models)}")

                await session.commit()
                logger.info("Reflection committed")
    except Exception as e:
        logger.error(f"Reflection failed: {e}", exc_info=True)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, runtime: AgentRuntime = Depends(get_runtime)) -> ChatResponse:
    response_text = await runtime.handle_message(
        child_id=req.child_id,
        message=req.message,
        history=req.history,
    )

    # Trigger Reflection Loop (background, don't block response)
    messages = list(req.history or [])
    messages.append({"role": "user", "content": req.message})
    messages.append({"role": "assistant", "content": response_text})
    asyncio.ensure_future(_run_reflection(req.child_id, messages))

    return ChatResponse(child_id=req.child_id, message=response_text)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, runtime: AgentRuntime = Depends(get_runtime)):
    """SSE streaming chat endpoint."""

    async def event_generator():
        response_text = await runtime.handle_message(
            child_id=req.child_id,
            message=req.message,
            history=req.history,
        )
        messages = list(req.history or [])
        messages.append({"role": "user", "content": req.message})
        messages.append({"role": "assistant", "content": response_text})
        asyncio.ensure_future(_run_reflection(req.child_id, messages))

        yield {"event": "message", "data": response_text}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())
