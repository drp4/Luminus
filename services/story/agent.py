"""Story Agent — three-stage pipeline: Plan → Generate → Judge.

All LLM calls run via run_in_executor to avoid SQLAlchemy greenlet conflicts.
"""

from __future__ import annotations

import asyncio
import json

from langchain_core.messages import HumanMessage, SystemMessage

from services.llm import create_llm

# ── Prompts (same as before, kept compact) ─────────────────────────────

PLANNER_PROMPT = """你是一个儿童故事策划师。根据孩子的兴趣和年龄设计互动故事大纲。

孩子：{child_info}  兴趣：{interests}  年龄：{age}岁

返回 JSON：
{{"title":"故事标题","theme":"主题","description":"一句话简介","difficulty_level":1-5,
 "characters":[{{"name":"角色名","personality":"性格","visual_seed":"英文外观词"}}],
 "chapters":[{{"order":1,"title":"章节名","summary":"概要"}}]}}
规则：3-5章，2-3个角色，围绕兴趣，正向价值观。只返回 JSON。"""

SCENE_PROMPT = """你是儿童故事作家。为场景生成内容和学习点。

故事《{story_title}》({story_theme}) 第{chapter_order}章"{chapter_title}" 第{scene_index}/{scenes}场景
前一场景：{previous}

返回 JSON：
{{"text":"场景叙述(200-400字，适合{age}岁)","image_prompt":"英文画面描述(50词)",
 "choices":[{{"text":"选项1"}},{{"text":"选项2"}},{{"text":"选项3(可选)"}}],
 "knowledge_points":[{{"subject":"学科","concept":"隐藏知识点","vocabulary":"关键词汇"}}]}}
规则：有画面感，2-3个选项，知识藏在故事里。只返回 JSON。"""

JUDGE_PROMPT = """评价儿童故事场景。场景：{scene}  年龄：{age}岁
评分(1-10)：趣味性/教育价值/年龄适配/选择质量
返回 JSON：{{"engagement":分,"education":分,"age_fit":分,"choices_quality":分,"total":均分,"pass":true/false,"feedback":"评语"}}
pass=true 需 total>=7.0。只返回 JSON。"""


def _run_sync(fn):
    """Run a sync function in a thread executor to avoid greenlet issues."""
    return asyncio.get_event_loop().run_in_executor(None, fn)


def _parse(content) -> dict:
    if isinstance(content, list):
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    if isinstance(content, str):
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
    return {}


class StoryAgent:

    def __init__(self):
        self._planner = create_llm(temperature=0.6, max_tokens=2048)
        self._writer = create_llm(temperature=0.8, max_tokens=2048)
        self._judge = create_llm(temperature=0.2, max_tokens=512)

    async def plan_story(self, child_nickname: str, child_age: int, interests: list[str], learning_style: str = "storytelling") -> dict:
        child_info = f"{child_nickname}, {child_age}岁, 风格={learning_style}"
        prompt = PLANNER_PROMPT.format(child_info=child_info, interests=", ".join(interests) if interests else "恐龙,太空", age=child_age)

        def _call():
            return self._planner.invoke([SystemMessage(content="只返回 JSON。"), HumanMessage(content=prompt)])
        response = await _run_sync(_call)
        return _parse(response.content)

    async def generate_scene(self, story_title: str, story_theme: str, chapter_order: int, chapter_title: str,
                              scene_index: int, scenes_per_chapter: int, previous_scene: str, child_age: int,
                              max_retries: int = 2) -> dict:
        prompt = SCENE_PROMPT.format(story_title=story_title, story_theme=story_theme, chapter_order=chapter_order,
                                      chapter_title=chapter_title, scene_index=scene_index, scenes=scenes_per_chapter,
                                      previous=previous_scene or "（故事开始）", age=child_age)

        for _ in range(max_retries + 1):
            def _write():
                return self._writer.invoke([SystemMessage(content="只返回 JSON。"), HumanMessage(content=prompt)])
            response = await _run_sync(_write)
            scene_data = _parse(response.content)

            if not scene_data or "text" not in scene_data:
                continue

            def _judge_call():
                return self._judge.invoke([SystemMessage(content="只返回 JSON。"),
                    HumanMessage(content=JUDGE_PROMPT.format(scene=scene_data.get("text", ""), age=child_age))])
            judge_resp = await _run_sync(_judge_call)
            result = _parse(judge_resp.content)

            if result and result.get("pass"):
                scene_data["_judge"] = result
                return scene_data

        return scene_data or {}
