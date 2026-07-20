from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import settings

engine = create_async_engine(settings.database_url, echo=settings.app_debug)
_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session


@asynccontextmanager
async def get_session_ctx() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session


async def init_db() -> None:
    """Create all tables — both ORM and raw memory table."""
    from services.models_base import Base
    from services.memory.store import MemoryStore

    # Import all model modules so they register on Base
    import services.profile.models  # noqa: F401
    import services.story.models    # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_session_ctx() as session:
        store = MemoryStore(session, mode=settings.vector_store)
        await store.ensure_table()


async def seed_defaults() -> None:
    """Seed default persona and agent configs."""
    from services.profile.models import AgentConfig, Persona

    async with get_session_ctx() as session:
        from sqlalchemy import select

        # Default persona
        existing = await session.execute(select(Persona).where(Persona.is_default == True))
        if not existing.scalar_one_or_none():
            session.add(Persona(
                id=uuid.uuid4(),
                name="小阳",
                personality="你是一个温暖、好奇、充满活力的AI伙伴。你像孩子同龄的朋友一样，喜欢探索世界的各种有趣事物。你总是用鼓励和欣赏的眼光看待孩子，真诚地为他们的每一点进步感到开心。",
                speaking_style="用同龄朋友的口吻说话，句子短而有趣，多用'我们'而不是'你'。适当使用语气词（哇、咦、哈哈）。像在聊天而不是在讲课。",
                age_feel="同龄",
                is_default=True,
            ))

        # Default agent configs
        for name, atype, prompt in [
            ("conversation", "conversation", "你是{persona_name}，一个陪伴孩子成长的AI伙伴。\n\n{persona_personality}\n\n## 关于和你聊天的孩子\n{human_block}\n\n## 你的说话方式\n{persona_speaking_style}\n\n## 规则\n1. 你是朋友，不是老师。\n2. 温暖鼓励，像同龄朋友。\n3. 顺着孩子兴趣聊。\n4. 用提问激发好奇心。\n5. 永远不要让孩子觉得在上课。\n6. 永远不直接给答案，用引导帮助孩子自己思考。"),
            ("teacher", "teacher", "你是{persona_name}，一个陪孩子探索世界的好奇伙伴。\n\n{persona_personality}\n\n## 关于和你一起探索的孩子\n{human_block}\n\n## 你的说话方式\n{persona_speaking_style}\n\n## 规则\n1. 用苏格拉底式提问引导孩子自己发现答案。\n2. 永远不直接给答案。\n3. 孩子遇到困难时先肯定再给提示。\n4. 把知识藏在对话里。\n5. 根据孩子水平和年龄调整难度。\n6. 永远不说'你错了'。"),
        ]:
            existing = await session.execute(select(AgentConfig).where(AgentConfig.name == name))
            if not existing.scalar_one_or_none():
                session.add(AgentConfig(
                    id=uuid.uuid4(),
                    name=name,
                    agent_type=atype,
                    system_prompt_template=prompt,
                ))

        await session.commit()
