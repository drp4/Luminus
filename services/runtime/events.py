from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable

Handler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    """Lightweight pub/sub event bus for MVP.

    Loop events flow through here — no direct coupling between components.
    """

    def __init__(self):
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler) -> None:
        self._handlers[event].append(handler)

    async def emit(self, event: str, data: dict[str, Any]) -> None:
        for handler in self._handlers.get(event, []):
            try:
                await handler(data)
            except Exception as e:
                # Log but don't let one handler break others
                import logging
                logging.getLogger("event_bus").error(f"Handler for {event} failed: {e}")

    def clear(self) -> None:
        self._handlers.clear()
