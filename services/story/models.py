from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.models_base import Base


class StoryStatus(str, Enum):
    draft = "draft"
    generating = "generating"
    ready = "ready"
    completed = "completed"


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("children.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    theme: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    target_age_min: Mapped[int] = mapped_column(default=6)
    target_age_max: Mapped[int] = mapped_column(default=12)
    status: Mapped[StoryStatus] = mapped_column(default=StoryStatus.draft)
    total_chapters: Mapped[int] = mapped_column(default=0)
    current_chapter: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    chapters: Mapped[list[Chapter]] = relationship(back_populates="story", order_by="Chapter.order")
    characters: Mapped[list[StoryCharacter]] = relationship(back_populates="story")

    # Growth alignment
    aligned_interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty_level: Mapped[int] = mapped_column(default=1)  # 1-5 aligned to vocabulary_level


class Chapter(Base):
    __tablename__ = "story_chapters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stories.id"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(default=1)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    story: Mapped[Story] = relationship(back_populates="chapters")
    scenes: Mapped[list[Scene]] = relationship(back_populates="chapter", order_by="Scene.order")


class Scene(Base):
    __tablename__ = "story_scenes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    chapter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("story_chapters.id"), nullable=False, index=True)
    order: Mapped[int] = mapped_column(default=1)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # Narrative text
    image_prompt: Mapped[str] = mapped_column(Text, default="")
    audio_url: Mapped[str] = mapped_column(String(500), default="")
    is_end_scene: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    chapter: Mapped[Chapter] = relationship(back_populates="scenes")
    choices: Mapped[list[Choice]] = relationship(back_populates="scene")
    knowledge_points: Mapped[list[KnowledgePoint]] = relationship(back_populates="scene")


class Choice(Base):
    __tablename__ = "story_choices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scene_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("story_scenes.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # Choice display text
    next_scene_order: Mapped[int | None] = mapped_column(nullable=True)  # Null = end of chapter

    scene: Mapped[Scene] = relationship(back_populates="choices")


class KnowledgePoint(Base):
    __tablename__ = "story_knowledge_points"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scene_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("story_scenes.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    concept: Mapped[str] = mapped_column(String(200), nullable=False)
    vocabulary: Mapped[str | None] = mapped_column(String(100), nullable=True)

    scene: Mapped[Scene] = relationship(back_populates="knowledge_points")


class StoryCharacter(Base):
    __tablename__ = "story_characters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    personality: Mapped[str] = mapped_column(Text, default="")
    visual_seed: Mapped[str] = mapped_column(String(200), default="")  # For consistent image generation

    story: Mapped[Story] = relationship(back_populates="characters")


class StorySession(Base):
    """Progress-tracking for multi-session stories."""

    __tablename__ = "story_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("children.id"), nullable=False, index=True)
    story_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stories.id"), nullable=False, index=True)
    current_chapter: Mapped[int] = mapped_column(default=1)
    current_scene_order: Mapped[int] = mapped_column(default=1)
    accumulated_choices: Mapped[list[str]] = mapped_column(JSON, default=list)
    story_summary: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_played_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
