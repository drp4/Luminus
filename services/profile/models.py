from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Float, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from services.models_base import Base


class VocabLevel(str, Enum):
    simple = "simple"
    moderate = "moderate"
    advanced = "advanced"


class LearningStyle(str, Enum):
    visual = "visual"
    storytelling = "storytelling"
    hands_on = "hands_on"
    questioning = "questioning"


class InterestTrend(str, Enum):
    rising = "rising"
    stable = "stable"
    declining = "declining"


class InterestSource(str, Enum):
    explicit_statement = "explicit_statement"
    implicit_clue = "implicit_clue"
    story_choice = "story_choice"


class Child(Base):
    __tablename__ = "children"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    grade: Mapped[str] = mapped_column(String(10), nullable=False)
    avatar_seed: Mapped[str] = mapped_column(String(50), default="default")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    speaking_style: Mapped[str] = mapped_column(Text, nullable=False)
    age_feel: Mapped[str] = mapped_column(String(20), nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False)


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    system_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    loop_config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)


class Capability(Base):
    __tablename__ = "capabilities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    capability_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    schema: Mapped[dict] = mapped_column(JSON, default=dict)


class ProfileSnapshot(Base):
    __tablename__ = "profile_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    vocabulary_level: Mapped[VocabLevel] = mapped_column(default=VocabLevel.simple)
    interests: Mapped[dict] = mapped_column(JSON, default=dict)
    curiosity_score: Mapped[float] = mapped_column(Float, default=0.5)
    expression_score: Mapped[float] = mapped_column(Float, default=0.5)
    reading_score: Mapped[float] = mapped_column(Float, default=0.5)
    thinking_score: Mapped[float] = mapped_column(Float, default=0.5)
    active_question_count: Mapped[int] = mapped_column(default=0)
    avg_session_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    emotion_trend: Mapped[dict] = mapped_column(JSON, default=dict)
    learning_style: Mapped[LearningStyle] = mapped_column(default=LearningStyle.storytelling)


class InterestModel(Base):
    __tablename__ = "interest_models"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=0.5)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    trend: Mapped[InterestTrend] = mapped_column(default=InterestTrend.stable)
    source: Mapped[InterestSource] = mapped_column(default=InterestSource.explicit_statement)
