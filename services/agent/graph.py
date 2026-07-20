from __future__ import annotations

import re
from typing import Literal

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from services.agent.agents.teacher import build_teacher_system_prompt
from services.agent.state import ConversationState
from services.llm import create_llm


def _extract_text(content) -> str:
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


def _build_chat_agent(state: ConversationState) -> dict:
    """Conversation Agent — warm friend for daily chat."""
    llm = create_llm(temperature=0.7, max_tokens=1024)
    persona = state.get("persona_block", "")
    human = state.get("human_block", "")
    system_prompt = f"""{persona}

## 关于和你聊天的孩子
{human}

## 规则
1. 你是朋友，不是老师。用温暖、鼓励的语气说话。
2. 顺着孩子兴趣聊，用提问激发好奇心。
3. 永远不要让孩子觉得在上课。
4. 保持回复简短有趣。
"""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state["messages"])
    response = llm.invoke(messages)
    return {
        "messages": state["messages"] + [{"role": "assistant", "content": _extract_text(response.content)}],
        "should_reflect": True,
        "agent_type": "chat",
    }


def _build_teacher_agent(state: ConversationState) -> dict:
    """Teacher Agent — progressive Socratic scaffolding."""
    llm = create_llm(temperature=0.5, max_tokens=1024)

    topic = _detect_topic(state)
    same_topic_turns = _count_same_topic_turns(state, topic)
    hint_level = min(same_topic_turns, 2)

    learning_style = _extract_learning_style(state.get("human_block", ""))
    child_age = _extract_age(state.get("human_block", ""))

    system_prompt = build_teacher_system_prompt(
        persona_block=state.get("persona_block", ""),
        human_block=state.get("human_block", ""),
        teaching_topic=topic,
        hint_level=hint_level,
        child_age=child_age,
        learning_style=learning_style,
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(state["messages"])
    response = llm.invoke(messages)

    return {
        "messages": state["messages"] + [{"role": "assistant", "content": _extract_text(response.content)}],
        "should_reflect": True,
        "agent_type": "teacher",
        "teaching_topic": topic,
        "hint_level": hint_level,
        "same_topic_turns": same_topic_turns + 1,
    }


def _detect_topic(state: ConversationState) -> str:
    last_user_msgs = [m["content"] for m in state["messages"][-4:] if m.get("role") == "user"]
    if not last_user_msgs:
        return "新话题"
    text = " ".join(last_user_msgs)
    topic_keywords = [
        "恐龙", "太空", "宇宙", "海洋", "动物", "植物", "科学", "数学",
        "画画", "音乐", "历史", "地理", "物理", "化学", "生物", "天文",
        "火山", "地震", "天气", "星球", "火箭", "机器人", "编程", "英语",
    ]
    found = [kw for kw in topic_keywords if kw in text]
    return found[0] if found else "新话题"


def _count_same_topic_turns(state: ConversationState, current_topic: str) -> int:
    if current_topic == "新话题":
        return 0
    prev = state.get("teaching_topic", "")
    prev_turns = state.get("same_topic_turns", 0)
    if prev == current_topic:
        return prev_turns
    return 0


def _extract_learning_style(human_block: str) -> str:
    for style in ("storytelling", "visual", "questioning", "hands_on"):
        if style in human_block:
            return style
    return "storytelling"


def _extract_age(human_block: str) -> int:
    match = re.search(r"(\d+)岁", human_block)
    return int(match.group(1)) if match else 9


def _intent_router(state: ConversationState) -> Literal["chat_agent", "teacher_agent"]:
    last_msg = state["messages"][-1]["content"].lower() if state["messages"] else ""
    education_keywords = [
        "为什么", "怎么", "教我", "什么是", "怎么做", "学习", "探索", "发现",
        "告诉我", "帮我", "我不知道", "好难", "不懂", "什么意思",
    ]
    if any(kw in last_msg for kw in education_keywords):
        return "teacher_agent"
    return "chat_agent"


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(ConversationState)
    graph.add_node("chat_agent", _build_chat_agent)
    graph.add_node("teacher_agent", _build_teacher_agent)
    graph.set_conditional_entry_point(
        _intent_router,
        {"chat_agent": "chat_agent", "teacher_agent": "teacher_agent"},
    )
    graph.add_edge("chat_agent", END)
    graph.add_edge("teacher_agent", END)
    return graph.compile()
