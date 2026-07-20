from __future__ import annotations

from typing import Any


class ToolRegistry:
    """Registry of all tools available to agents.

    Tools are grouped by Capability. MVP is flat list; Capability grouping is
    a future upgrade path (to MCP, third-party APIs, etc.).
    """

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}
        self._implementations: dict[str, Any] = {}

    def register(self, name: str, description: str, schema: dict, func: Any, capability: str = "default") -> None:
        self._tools[name] = {
            "name": name,
            "description": description,
            "schema": schema,
            "capability": capability,
        }
        self._implementations[name] = func

    def get_llm_tools(self, agent_type: str) -> list[dict]:
        """Return tools in OpenAI function-calling format for a given agent type."""
        agent_tools = {
            "conversation": ["search_memory", "save_memory", "get_child_info"],
            "teacher": ["search_memory", "get_child_info"],
            "memory": [],
        }
        allowed = set(agent_tools.get(agent_type, []))

        tools = []
        for name, info in self._tools.items():
            if not allowed or name in allowed:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": info["name"],
                        "description": info["description"],
                        "parameters": info["schema"],
                    },
                })
        return tools

    def execute(self, name: str, **kwargs: Any) -> Any:
        func = self._implementations.get(name)
        if func is None:
            raise ValueError(f"Tool '{name}' not found in registry")
        return func(**kwargs)


# Global singleton for MVP
tool_registry = ToolRegistry()
