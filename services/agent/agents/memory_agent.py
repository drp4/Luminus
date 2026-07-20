from __future__ import annotations

import hashlib
import json
import math

from langchain_core.messages import HumanMessage, SystemMessage

from services.llm import create_llm
from services.memory.store import MemoryStore

MEMORY_EXTRACTION_PROMPT = """你是一个记忆提取器。分析下面的对话，提取关于孩子的关键信息。

返回一个 JSON 数组，每个元素包含：
- "fact": 一条关于孩子的事实（中文，简洁，一条完整信息）
- "type": 类型，只能是 "interest"(兴趣), "personality"(性格), "knowledge"(知识水平), "emotion"(情绪), "fact"(基本信息)
- "importance": 重要性 0.0-1.0

规则：
1. 只提取关于孩子的信息，不提取 AI 说了什么
2. 按重要性排序，只返回重要的信息（importance >= 0.3）
3. 如果孩子表达了对某个话题的兴奋/好奇 → type=interest, importance >= 0.6
4. 如果孩子提到了自己的喜好、习惯、特点 → type=personality
5. 如果孩子展示了某个领域的知识 → type=knowledge
6. 如果孩子表达了强烈情绪 → type=emotion
7. 基本信息（名字、年龄等）→ type=fact, importance=0.5
8. 没有值得记的信息时返回空数组 []
9. 只返回 JSON 数组，不要其他内容

示例输入：
孩子: 我特别喜欢恐龙！霸王龙最厉害了，它的牙齿有15厘米长！
AI: 哇，你对恐龙好了解啊！

示例输出：
[{"fact": "孩子对恐龙有强烈兴趣，特别喜欢霸王龙", "type": "interest", "importance": 0.9}, {"fact": "孩子知道霸王龙牙齿有15厘米长，恐龙知识丰富", "type": "knowledge", "importance": 0.7}]"""


MEMORY_MERGE_PROMPT = """你是一个记忆合并器。判断一条新的记忆是否与已有记忆冲突或重复。

已有记忆：
{existing}

新记忆：
{new_fact}

选择操作：
- "insert": 新记忆是全新信息，直接添加
- "update": 新记忆是已有记忆的更新/补充，替换旧记忆（给出合并后的文本）
- "skip": 新记忆与已有记忆重复，无需操作

只返回 JSON：{"action": "insert|update|skip", "merged_text": "合并后的文本（仅 update 时需要）"}"""


class SimpleEmbeddings:
    """Fallback embedding using character n-gram hashing."""

    def __init__(self, dim: int = 256):
        self._dim = dim

    async def aembed_query(self, text: str) -> list[float]:
        return self._hash_embed(text)

    def _hash_embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        text = text.lower()
        for n in (2, 3, 4):
            for i in range(len(text) - n + 1):
                ngram = text[i:i + n]
                idx = int(hashlib.md5(ngram.encode()).hexdigest(), 16) % self._dim
                vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


class MemoryAgent:
    """Background agent for Reflection and Growth Loops.

    Uses LLM-based structured extraction to pull facts from conversations.
    """

    def __init__(self, memory_store: MemoryStore):
        self._store = memory_store
        self._embeddings = SimpleEmbeddings(dim=256)
        self._llm = create_llm(temperature=0.1, max_tokens=1024)

    async def reflect(self, child_id: str, conversation_turns: list[dict]) -> list[dict]:
        """Extract structured facts from conversation and persist to long_memories.

        Returns list of saved memory dicts with {fact, type, importance}.
        """
        saved: list[dict] = []

        text = "\n".join(
            f"{'孩子' if t.get('role') == 'user' else 'AI'}: {t.get('content', '')}"
            for t in conversation_turns[-10:]
        )
        if not text.strip():
            return saved

        # 1. Extract structured facts via LLM
        facts = await self._extract_facts(text)
        if not facts:
            return saved

        # 2. For each fact: check similarity → decide merge/insert → save
        for item in facts:
            fact_text = item["fact"]
            fact_type = item.get("type", "fact")
            importance = item.get("importance", 0.5)

            embedding = await self._embeddings.aembed_query(fact_text)

            # Find similar existing memories
            existing = await self._store.search(
                child_id=child_id,
                query_embedding=embedding,
                top_k=2,
                threshold=0.75,
            )

            if existing:
                # Use LLM to decide merge/update/skip
                action, merged = await self._merge_decision(existing[0]["content"], fact_text)
                if action == "skip":
                    continue
                if action == "update" and merged:
                    fact_text = merged
                    # Delete old, insert new merged version
                    await self._store.delete(existing[0]["id"])

            await self._store.add(
                child_id=child_id,
                content=fact_text,
                embedding=embedding,
                memory_type=fact_type,
                importance=importance,
            )
            saved.append(item)

        return saved

    async def _extract_facts(self, conversation_text: str) -> list[dict]:
        """LLM-based structured fact extraction."""
        try:
            response = self._llm.invoke([
                SystemMessage(content=MEMORY_EXTRACTION_PROMPT),
                HumanMessage(content=conversation_text),
            ])
            content = self._extract_text(response.content)
            # Parse JSON array from response
            content = content.strip()
            if content.startswith("```"):
                # Strip markdown code block
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return []

    async def _merge_decision(self, existing_fact: str, new_fact: str) -> tuple[str, str | None]:
        """LLM decides whether to insert, update, or skip."""
        try:
            prompt = MEMORY_MERGE_PROMPT.format(existing=existing_fact, new_fact=new_fact)
            response = self._llm.invoke(prompt)
            content = self._extract_text(response.content).strip()
            result = json.loads(content)
            return result.get("action", "insert"), result.get("merged_text")
        except (json.JSONDecodeError, Exception):
            return "insert", None

    async def search_relevant_memories(self, child_id: str, query: str, top_k: int = 5) -> list[dict]:
        embedding = await self._embeddings.aembed_query(query)
        return await self._store.search(child_id=child_id, query_embedding=embedding, top_k=top_k)

    @staticmethod
    def _extract_text(content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "".join(parts)
        return str(content)
