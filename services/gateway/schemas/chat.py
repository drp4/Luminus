from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    child_id: str
    message: str
    history: list[dict] | None = None


class ChatResponse(BaseModel):
    child_id: str
    message: str


class ChildCreateRequest(BaseModel):
    nickname: str
    age: int
    grade: str


class ChildResponse(BaseModel):
    id: str
    nickname: str
    age: int
    grade: str
