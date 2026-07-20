from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MemoryStore:
    """Long-term memory store with dual backend support.

    - "simple" mode (SQLite): stores embeddings as JSON, linear-scan search. MVP default.
    - "pgvector" mode (PostgreSQL): native vector index for production.
    """

    def __init__(self, session: AsyncSession, mode: str = "simple", embedding_dim: int = 1536):
        self._session = session
        self._mode = mode
        self._embedding_dim = embedding_dim

    async def ensure_table(self) -> None:
        if self._mode == "pgvector":
            await self._session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await self._session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS long_memories (
                    id TEXT PRIMARY KEY,
                    child_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector({self._embedding_dim}),
                    memory_type TEXT NOT NULL DEFAULT 'fact',
                    importance REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{{}}'
                )
            """))
        else:
            await self._session.execute(text("""
                CREATE TABLE IF NOT EXISTS long_memories (
                    id TEXT PRIMARY KEY,
                    child_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    memory_type TEXT NOT NULL DEFAULT 'fact',
                    importance REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """))
        await self._session.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_long_memories_child ON long_memories(child_id)"
        ))

    async def add(
        self,
        child_id: uuid.UUID,
        content: str,
        embedding: list[float],
        memory_type: str = "fact",
        importance: float = 0.5,
        metadata: dict | None = None,
    ) -> uuid.UUID:
        memory_id = uuid.uuid4()
        now = datetime.now(timezone.utc).isoformat()
        emb_str = json.dumps(embedding)

        if self._mode == "pgvector":
            await self._session.execute(
                text("""
                    INSERT INTO long_memories (id, child_id, content, embedding, memory_type, importance, created_at, metadata)
                    VALUES (:id, :child_id, :content, :embedding, :memory_type, :importance, :created_at, :metadata)
                """),
                {
                    "id": str(memory_id),
                    "child_id": str(child_id),
                    "content": content,
                    "embedding": json.dumps(embedding),
                    "memory_type": memory_type,
                    "importance": importance,
                    "created_at": now,
                    "metadata": json.dumps(metadata or {}),
                },
            )
        else:
            await self._session.execute(
                text("""
                    INSERT INTO long_memories (id, child_id, content, embedding, memory_type, importance, created_at, metadata)
                    VALUES (:id, :child_id, :content, :embedding, :memory_type, :importance, :created_at, :metadata)
                """),
                {
                    "id": str(memory_id),
                    "child_id": str(child_id),
                    "content": content,
                    "embedding": emb_str,
                    "memory_type": memory_type,
                    "importance": importance,
                    "created_at": now,
                    "metadata": json.dumps(metadata or {}),
                },
            )
        return memory_id

    async def search(
        self,
        child_id: uuid.UUID,
        query_embedding: list[float],
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[dict]:
        if self._mode == "pgvector":
            return await self._pgvector_search(child_id, query_embedding, top_k, threshold)
        return await self._simple_search(child_id, query_embedding, top_k, threshold)

    async def _pgvector_search(
        self, child_id: uuid.UUID, query_embedding: list[float], top_k: int, threshold: float
    ) -> list[dict]:
        result = await self._session.execute(
            text("""
                SELECT id, content, memory_type, importance, created_at,
                       1 - (embedding <=> :embedding) AS similarity
                FROM long_memories
                WHERE child_id = :child_id
                  AND 1 - (embedding <=> :embedding) > :threshold
                ORDER BY embedding <=> :embedding
                LIMIT :top_k
            """),
            {
                "child_id": str(child_id),
                "embedding": json.dumps(query_embedding),
                "threshold": threshold,
                "top_k": top_k,
            },
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def _simple_search(
        self, child_id: uuid.UUID, query_embedding: list[float], top_k: int, threshold: float
    ) -> list[dict]:
        """Linear scan with cosine similarity — fine for MVP data volumes."""
        result = await self._session.execute(
            text("""
                SELECT id, content, memory_type, importance, created_at, embedding
                FROM long_memories
                WHERE child_id = :child_id
            """),
            {"child_id": str(child_id)},
        )
        rows = result.fetchall()
        scored: list[dict] = []
        for row in rows:
            emb_data = row._mapping.get("embedding")
            if not emb_data:
                continue
            emb = json.loads(emb_data) if isinstance(emb_data, str) else emb_data
            sim = self._cosine_similarity(query_embedding, emb)
            if sim >= threshold:
                scored.append({
                    "id": row._mapping["id"],
                    "content": row._mapping["content"],
                    "memory_type": row._mapping["memory_type"],
                    "importance": row._mapping["importance"],
                    "created_at": row._mapping["created_at"],
                    "similarity": sim,
                })
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    async def delete(self, memory_id: uuid.UUID) -> None:
        await self._session.execute(
            text("DELETE FROM long_memories WHERE id = :id"),
            {"id": str(memory_id)},
        )

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
