from __future__ import annotations

import asyncio
from typing import Any


class LoopScheduler:
    """Manages the three Loop cycles.

    - Interaction Loop: real-time, handled inline by agents (not scheduled here)
    - Reflection Loop: triggered by conversation.ended event
    - Growth Loop: scheduled daily/weekly
    """

    def __init__(self, event_bus: Any = None, memory_agent: Any = None):
        self._event_bus = event_bus
        self._memory_agent = memory_agent
        self._daily_task: asyncio.Task | None = None

    def wire(self) -> None:
        """Wire event handlers to the event bus."""
        if self._event_bus:
            self._event_bus.subscribe("conversation.ended", self._on_conversation_ended)

    async def _on_conversation_ended(self, data: dict[str, Any]) -> None:
        """Handle conversation.ended → trigger Reflection Loop."""
        if not self._memory_agent:
            return

        child_id = data.get("child_id", "")
        messages = data.get("messages", [])

        new_memories = await self._memory_agent.reflect(child_id, messages)
        if new_memories and self._event_bus:
            await self._event_bus.emit("reflection.completed", {
                "child_id": child_id,
                "new_memories": new_memories,
            })
            await self._event_bus.emit("interest.check", {
                "child_id": child_id,
            })

    async def start_growth_loop(self, interval_hours: int = 24) -> None:
        """Start periodic Growth Loop (demo stub)."""
        while True:
            await asyncio.sleep(interval_hours * 3600)
            if self._event_bus:
                await self._event_bus.emit("growth.cycle.tick", {
                    "timestamp": "now",
                })
