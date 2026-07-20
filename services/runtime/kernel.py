from __future__ import annotations

import uuid
from typing import Any

from services.agent.graph import build_graph
from services.agent.state import ConversationState


def _extract_content(content: Any) -> str:
    """Handle both string and structured content block responses."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts)
    return str(content)


class AgentRuntime:
    """AOS Kernel — the single entry point for all agent interactions.

    Responsibilities:
    - Context assembly (Persona Block + Human Block + message history)
    - Persona injection
    - Human Block injection (via Profile Engine)
    - Tool Registry management
    - Agent lifecycle (create → run → destroy)
    - Loop scheduling
    - Event dispatch
    - Guardrails (input/output filtering)
    """

    def __init__(
        self,
        child_repo: Any = None,
        persona_repo: Any = None,
        profile_repo: Any = None,
        profile_engine: Any = None,
        memory_agent: Any = None,
        event_bus: Any = None,
        guard: Any = None,
    ):
        self._child_repo = child_repo
        self._persona_repo = persona_repo
        self._profile_repo = profile_repo
        self._profile_engine = profile_engine
        self._memory_agent = memory_agent
        self._event_bus = event_bus
        self._guard = guard
        self._graph = build_graph()

    async def handle_message(
        self,
        child_id: str,
        message: str,
        history: list[dict] | None = None,
    ) -> str:
        """Process a single message through the full Runtime pipeline."""
        child_uuid = uuid.UUID(child_id)

        # 1. Load context
        persona_block = await self._build_persona_block()
        human_block = await self._build_human_block(child_uuid)

        # 2. Input guardrail
        if self._guard:
            message = self._guard.filter_input(message)

        # 3. Assemble state
        messages = list(history or [])
        messages.append({"role": "user", "content": message})

        state: ConversationState = {
            "child_id": child_id,
            "persona_block": persona_block,
            "human_block": human_block,
            "messages": messages,
            "agent_type": "chat",
            "tool_results": [],
            "should_reflect": False,
            "teaching_topic": "新话题",
            "hint_level": 0,
            "same_topic_turns": 0,
        }

        # 4. Invoke StateGraph
        result = await self._graph.ainvoke(state)

        # 5. Output guardrail
        response_text = ""
        result_messages = result.get("messages", [])
        if result_messages:
            last = result_messages[-1]
            content = last.get("content", "") if isinstance(last, dict) else getattr(last, "content", "")
            response_text = _extract_content(content)

        if self._guard:
            response_text = self._guard.filter_output(response_text)

        # 6. Emit events
        if self._event_bus:
            await self._event_bus.emit("conversation.turn.added", {
                "child_id": child_id,
                "message": message,
                "response": response_text,
            })

            if result.get("should_reflect"):
                await self._event_bus.emit("conversation.ended", {
                    "child_id": child_id,
                    "messages": result_messages,
                })

        return response_text

    async def _build_persona_block(self) -> str:
        if self._persona_repo:
            persona = await self._persona_repo.get_default()
            if persona:
                return f"你是{persona.name}。{persona.personality}\n说话方式: {persona.speaking_style}"
        return "你是一个陪伴孩子成长的AI伙伴。"

    async def _build_human_block(self, child_uuid: uuid.UUID) -> str:
        if not (self._child_repo and self._profile_repo and self._profile_engine):
            return ""

        child = await self._child_repo.get(child_uuid)
        if not child:
            return ""

        snapshot = await self._profile_repo.get_latest_snapshot(child_uuid)
        interests = await self._profile_repo.get_interests(child_uuid)
        persona = await self._persona_repo.get_default() if self._persona_repo else None

        return self._profile_engine.generate_human_block(
            child_nickname=child.nickname,
            child_age=child.age,
            snapshot=snapshot,
            interests=interests,
            personality_name=persona.name if persona else "伙伴",
        )
