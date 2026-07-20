from typing import TypedDict


class ConversationState(TypedDict):
    child_id: str
    persona_block: str
    human_block: str
    messages: list[dict]
    agent_type: str
    tool_results: list[dict]
    should_reflect: bool
    # Teaching context for progressive scaffolding
    teaching_topic: str       # Current topic being explored
    hint_level: int           # 0=first attempt, 1=second, 2=third+
    same_topic_turns: int     # How many turns on the same topic
