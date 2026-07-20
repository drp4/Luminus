"""Story API — interactive AI-generated stories with branching."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.database import get_session_ctx
from services.profile.repository import ChildRepo, ProfileRepo
from services.story.agent import StoryAgent
from services.story.models import (
    Chapter,
    Choice,
    KnowledgePoint,
    Scene,
    Story,
    StoryCharacter,
    StorySession,
    StoryStatus,
)

router = APIRouter(prefix="/stories", tags=["story"])

_story_agent = StoryAgent()


# ── Schemas ────────────────────────────────────────────────────────────

class StoryCreateRequest(BaseModel):
    child_id: str


class StoryOutlineResponse(BaseModel):
    id: str
    title: str
    theme: str
    description: str
    status: str
    difficulty_level: int
    characters: list[dict]
    chapters: list[dict]


class SceneResponse(BaseModel):
    id: str
    order: int
    text: str
    image_prompt: str
    choices: list[dict]
    knowledge_points: list[dict]
    is_end_scene: bool


class ChoiceRequest(BaseModel):
    child_id: str
    choice_text: str


class StoryListResponse(BaseModel):
    stories: list[dict]


# ── Routes ─────────────────────────────────────────────────────────────

@router.post("", response_model=StoryOutlineResponse)
async def create_story(req: StoryCreateRequest) -> StoryOutlineResponse:
    """Create a new story based on the child's interests and profile."""
    child_uuid = uuid.UUID(req.child_id)

    async with get_session_ctx() as session:
        child_repo = ChildRepo(session)
        child = await child_repo.get(child_uuid)
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")

        profile_repo = ProfileRepo(session)
        interests = await profile_repo.get_interests(child_uuid)
        interest_topics = [i.topic for i in interests] if interests else ["恐龙", "太空"]
        snapshot = await profile_repo.get_latest_snapshot(child_uuid)

        # Stage 1: Plan story
        plan = await _story_agent.plan_story(
            child_nickname=child.nickname,
            child_age=child.age,
            interests=interest_topics,
            learning_style=snapshot.learning_style.value if snapshot else "storytelling",
        )

        if not plan or "title" not in plan:
            # Fallback plan
            plan = {
                "title": f"{child.nickname}的{interest_topics[0]}大冒险",
                "theme": interest_topics[0],
                "description": f"一个关于{interest_topics[0]}的有趣故事",
                "difficulty_level": 2,
                "characters": [
                    {"name": child.nickname, "personality": "好奇勇敢的小探险家", "visual_seed": "young explorer"},
                    {"name": "小阳", "personality": "温暖的AI伙伴", "visual_seed": "friendly companion robot"},
                ],
                "chapters": [
                    {"order": 1, "title": "奇妙的开始", "summary": "主人公发现了一个神秘的线索"},
                    {"order": 2, "title": "探索之旅", "summary": "在实践中学习和成长"},
                    {"order": 3, "title": "收获与成长", "summary": "故事的温暖结局"},
                ],
            }

        # Save to DB
        story = Story(
            child_id=child_uuid,
            title=plan["title"],
            theme=plan.get("theme", interest_topics[0]),
            description=plan.get("description", ""),
            target_age_min=max(child.age - 2, 4),
            target_age_max=child.age + 2,
            status=StoryStatus.draft,
            total_chapters=len(plan.get("chapters", [])),
            aligned_interests=interest_topics,
            difficulty_level=plan.get("difficulty_level", 2),
        )
        session.add(story)
        await session.flush()  # Generate story.id before creating chapters

        # Characters
        character_map: dict[str, StoryCharacter] = {}
        for char_data in plan.get("characters", []):
            char = StoryCharacter(
                story_id=story.id,
                name=char_data["name"],
                personality=char_data.get("personality", ""),
                visual_seed=char_data.get("visual_seed", ""),
            )
            session.add(char)
            character_map[char.name] = char

        # Chapters (outline only, scenes generated on demand)
        chapters_outline = []
        for ch_data in plan.get("chapters", []):
            chapter = Chapter(
                story_id=story.id,
                order=ch_data.get("order", 1),
                title=ch_data.get("title", f"第{ch_data.get('order',1)}章"),
                summary=ch_data.get("summary", ""),
            )
            session.add(chapter)
            chapters_outline.append({
                "order": chapter.order,
                "title": chapter.title,
                "summary": chapter.summary,
            })

        await session.commit()

        return StoryOutlineResponse(
            id=str(story.id),
            title=story.title,
            theme=story.theme,
            description=story.description,
            status=story.status.value,
            difficulty_level=story.difficulty_level,
            characters=[{"name": c.name, "personality": c.personality} for c in character_map.values()],
            chapters=chapters_outline,
        )


@router.get("")
async def list_stories(child_id: str) -> StoryListResponse:
    """List all stories for a child."""
    child_uuid = uuid.UUID(child_id)

    async with get_session_ctx() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Story).where(Story.child_id == child_uuid).order_by(Story.updated_at.desc())
        )
        stories = result.scalars().all()

        return StoryListResponse(stories=[
            {
                "id": str(s.id),
                "title": s.title,
                "theme": s.theme,
                "description": s.description,
                "status": s.status.value,
                "total_chapters": s.total_chapters,
                "current_chapter": s.current_chapter,
                "created_at": s.created_at.isoformat() if s.created_at else "",
            }
            for s in stories
        ])


@router.get("/{story_id}")
async def get_story(story_id: str) -> dict:
    """Get full story details with all chapters and scenes."""
    story_uuid = uuid.UUID(story_id)

    async with get_session_ctx() as session:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(Story).options(selectinload(Story.chapters).selectinload(Chapter.scenes))
            .where(Story.id == story_uuid)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")

        # Get session progress
        session_result = await session.execute(
            select(StorySession).where(StorySession.story_id == story_uuid).order_by(StorySession.last_played_at.desc()).limit(1)
        )
        sess = session_result.scalar_one_or_none()

        chapters_data = []
        for ch in sorted(story.chapters, key=lambda c: c.order):
            scenes_data = []
            for sc in sorted(ch.scenes, key=lambda s: s.order):
                scenes_data.append({
                    "id": str(sc.id),
                    "order": sc.order,
                    "text": sc.text,
                    "image_prompt": sc.image_prompt,
                    "choices": [{"text": c.text} for c in sc.choices],
                    "knowledge_points": [
                        {"subject": kp.subject, "concept": kp.concept, "vocabulary": kp.vocabulary}
                        for kp in sc.knowledge_points
                    ],
                    "is_end_scene": sc.is_end_scene,
                })
            chapters_data.append({
                "order": ch.order,
                "title": ch.title,
                "summary": ch.summary,
                "scenes": scenes_data,
            })

        return {
            "id": str(story.id),
            "title": story.title,
            "theme": story.theme,
            "description": story.description,
            "status": story.status.value,
            "difficulty_level": story.difficulty_level,
            "characters": [{"name": c.name, "personality": c.personality} for c in story.characters],
            "chapters": chapters_data,
            "session": {
                "current_chapter": sess.current_chapter if sess else 1,
                "current_scene": sess.current_scene_order if sess else 1,
            } if sess else None,
        }


@router.post("/{story_id}/scene")
async def generate_next_scene(story_id: str, chapter_order: int = 1, scene_index: int = 1) -> SceneResponse:
    """Generate the next scene in a chapter (Stage 2: Scene Generator)."""
    story_uuid = uuid.UUID(story_id)

    # Step 1: Read story data (separate session, closed before LLM call)
    async with get_session_ctx() as session:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(Story).options(selectinload(Story.chapters).selectinload(Chapter.scenes))
            .where(Story.id == story_uuid)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")

        chapter = next((ch for ch in story.chapters if ch.order == chapter_order), None)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        prev_text = ""
        if scene_index > 1:
            prev_scene = next((s for s in chapter.scenes if s.order == scene_index - 1), None)
            if prev_scene:
                prev_text = prev_scene.text[:300]

        story_info = {
            "title": story.title,
            "theme": story.theme,
            "target_age": story.target_age_min,
            "total_chapters": story.total_chapters,
            "chapter_id": str(chapter.id),
        }

    # Step 2: Generate scene via LLM (outside DB session)
    scene_data = await _story_agent.generate_scene(
        story_title=story_info["title"],
        story_theme=story_info["theme"],
        chapter_order=chapter_order,
        chapter_title=chapter.title,
        scene_index=scene_index,
        scenes_per_chapter=3,
        previous_scene=prev_text,
        child_age=story_info["target_age"],
    )

    if not scene_data or "text" not in scene_data:
        raise HTTPException(status_code=500, detail="Scene generation failed")

    # Step 3: Save scene (new session)
    async with get_session_ctx() as session:
        is_end = scene_index >= 3 and chapter_order >= story_info["total_chapters"]
        scene = Scene(
            chapter_id=uuid.UUID(story_info["chapter_id"]),
            order=scene_index,
            text=scene_data["text"],
            image_prompt=scene_data.get("image_prompt", ""),
            is_end_scene=is_end,
        )
        session.add(scene)
        await session.flush()

        choices_data = []
        for choice_data in scene_data.get("choices", [])[:3]:
            choice = Choice(scene_id=scene.id, text=choice_data["text"])
            session.add(choice)
            choices_data.append({"text": choice.text})

        kp_data = []
        for kp in scene_data.get("knowledge_points", []):
            kp_obj = KnowledgePoint(
                scene_id=scene.id,
                subject=kp.get("subject", ""),
                concept=kp.get("concept", ""),
                vocabulary=kp.get("vocabulary"),
            )
            session.add(kp_obj)
            kp_data.append({"subject": kp_obj.subject, "concept": kp_obj.concept, "vocabulary": kp_obj.vocabulary})

        # Update story status
        from sqlalchemy import update
        new_status = StoryStatus.completed.value if is_end else StoryStatus.ready.value
        await session.execute(
            update(Story).where(Story.id == story_uuid).values(status=new_status)
        )
        await session.commit()

        return SceneResponse(
            id=str(scene.id), order=scene.order, text=scene.text,
            image_prompt=scene.image_prompt, choices=choices_data,
            knowledge_points=kp_data, is_end_scene=scene.is_end_scene,
        )


@router.post("/{story_id}/choose")
async def make_choice(story_id: str, req: ChoiceRequest) -> SceneResponse:
    """Make a choice and generate the next scene."""
    story_uuid = uuid.UUID(story_id)

    async with get_session_ctx() as session:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(Story).options(selectinload(Story.chapters).selectinload(Chapter.scenes))
            .where(Story.id == story_uuid)
        )
        story = result.scalar_one_or_none()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")

        child_uuid = uuid.UUID(req.child_id)

        # Get or create session
        sess_result = await session.execute(
            select(StorySession).where(
                StorySession.story_id == story_uuid,
                StorySession.child_id == child_uuid,
            ).order_by(StorySession.last_played_at.desc()).limit(1)
        )
        sess = sess_result.scalar_one_or_none()

        if not sess:
            sess = StorySession(
                child_id=child_uuid,
                story_id=story_uuid,
                current_chapter=1,
                current_scene_order=1,
                accumulated_choices=[],
            )
            session.add(sess)

        # Record the choice
        sess.accumulated_choices.append(req.choice_text)
        next_order = sess.current_scene_order + 1

        # Check if we need a new chapter
        current_chapter = sess.current_chapter
        scene_count_in_chapter = sum(1 for ch in story.chapters if ch.order == current_chapter for _ in ch.scenes)
        if next_order > scene_count_in_chapter + 1:  # +1 for the newly generated scene
            if current_chapter < story.total_chapters:
                current_chapter += 1
                next_order = 1
            else:
                # End of story
                sess.current_scene_order = next_order - 1
                sess.story_summary = f"完成故事《{story.title}》"
                await session.commit()
                from fastapi.responses import JSONResponse
                return JSONResponse({"message": "故事已完成！", "finished": True})

        # Generate next scene
        chapter = next((ch for ch in story.chapters if ch.order == current_chapter), None)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        prev_scene = next((s for s in sorted(chapter.scenes, key=lambda x: x.order)
                          if s.order == next_order - 1), None)
        prev_text = prev_scene.text[:300] if prev_scene else ""

        scene_data = await _story_agent.generate_scene(
            story_title=story.title,
            story_theme=story.theme,
            chapter_order=current_chapter,
            chapter_title=chapter.title,
            scene_index=next_order,
            scenes_per_chapter=3,
            previous_scene=prev_text,
            child_age=story.target_age_min,
        )

        if not scene_data or "text" not in scene_data:
            raise HTTPException(status_code=500, detail="Scene generation failed")

        is_end = current_chapter >= story.total_chapters and next_order >= 3
        scene = Scene(
            chapter_id=chapter.id,
            order=next_order,
            text=scene_data["text"],
            image_prompt=scene_data.get("image_prompt", ""),
            is_end_scene=is_end,
        )
        session.add(scene)

        # Choices and knowledge points
        choices_data = []
        for choice_data in scene_data.get("choices", [])[:3]:
            choice = Choice(scene_id=scene.id, text=choice_data["text"])
            session.add(choice)
            choices_data.append({"text": choice.text})

        kp_data = []
        for kp in scene_data.get("knowledge_points", []):
            kp_obj = KnowledgePoint(
                scene_id=scene.id,
                subject=kp.get("subject", ""),
                concept=kp.get("concept", ""),
                vocabulary=kp.get("vocabulary"),
            )
            session.add(kp_obj)
            kp_data.append({"subject": kp_obj.subject, "concept": kp_obj.concept, "vocabulary": kp_obj.vocabulary})

        # Update session
        sess.current_chapter = current_chapter
        sess.current_scene_order = next_order
        if is_end:
            story.status = StoryStatus.completed

        await session.commit()

        return SceneResponse(
            id=str(scene.id),
            order=scene.order,
            text=scene.text,
            image_prompt=scene.image_prompt,
            choices=choices_data,
            knowledge_points=kp_data,
            is_end_scene=scene.is_end_scene,
        )
