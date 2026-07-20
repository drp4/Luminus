from pydantic import BaseModel


class InterestItem(BaseModel):
    topic: str
    weight: float
    trend: str


class SnapshotItem(BaseModel):
    recorded_at: str
    vocabulary_level: str
    curiosity_score: float
    expression_score: float
    reading_score: float
    thinking_score: float
    learning_style: str
    emotion_trend: dict


class MemoryItem(BaseModel):
    memory_type: str
    importance: float
    content: str
    created_at: str


class ProfileResponse(BaseModel):
    child_id: str
    nickname: str
    age: int
    grade: str
    snapshot: SnapshotItem | None
    interests: list[InterestItem]
    recent_memories: list[MemoryItem]


class GardenPlant(BaseModel):
    topic: str
    weight: float
    trend: str
    stage: str  # "seed", "sprout", "growing", "blooming"
    color: str


class GardenResponse(BaseModel):
    child_id: str
    nickname: str
    plants: list[GardenPlant]
    soil_quality: float  # average of all growth scores
    garden_level: int    # 1-5 based on overall progress
    total_memories: int
