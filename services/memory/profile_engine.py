from __future__ import annotations

import uuid

from services.profile.models import InterestModel, InterestSource, InterestTrend, LearningStyle, ProfileSnapshot, VocabLevel


class ProfileEngine:
    """Computational layer between GrowthProfile tables and Human Block."""

    MAX_HUMAN_BLOCK_CHARS = 500

    def generate_human_block(
        self,
        child_nickname: str,
        child_age: int,
        snapshot: ProfileSnapshot | None,
        interests: list[InterestModel],
        personality_name: str,
    ) -> str:
        parts: list[str] = []
        parts.append(f"{child_nickname}, {child_age}岁。")
        parts.append(f"你的伙伴人格是「{personality_name}」，请用符合这个人格的语气说话。")
        if snapshot:
            parts.append(self._summarize_snapshot(snapshot))
        if interests:
            parts.append(self._summarize_interests(interests))
        parts.append(self._guidance(snapshot))
        block = "\n".join(parts)
        if len(block) > self.MAX_HUMAN_BLOCK_CHARS:
            block = block[: self.MAX_HUMAN_BLOCK_CHARS - 3] + "..."
        return block

    def _summarize_snapshot(self, s: ProfileSnapshot) -> str:
        return (
            f"词汇水平: {s.vocabulary_level.value}。"
            f"好奇心: {s.curiosity_score:.1%}。"
            f"表达能力: {s.expression_score:.1%}。"
            f"思考能力: {s.thinking_score:.1%}。"
            f"学习风格偏好: {s.learning_style.value}。"
            f"最近情绪趋势: {self._top_emotion(s.emotion_trend)}。"
        )

    def _summarize_interests(self, interests: list[InterestModel]) -> str:
        rising = [i.topic for i in interests if i.trend == InterestTrend.rising]
        stable = [i.topic for i in interests if i.trend == InterestTrend.stable]
        parts = []
        if rising:
            parts.append(f"最近特别感兴趣的: {', '.join(rising)}。")
        if stable:
            parts.append(f"一直在关注的: {', '.join(stable)}。")
        return " ".join(parts) if parts else ""

    def _guidance(self, snapshot: ProfileSnapshot | None) -> str:
        lines = [
            "注意: 你是一个陪伴孩子成长的AI伙伴，不是老师。",
            "永远用引导的方式，不要直接给答案。",
            "如果孩子表现出好奇心，鼓励他/她继续探索。",
            "永远不要让孩子觉得'在上课'。",
        ]
        if snapshot:
            match snapshot.learning_style:
                case LearningStyle.storytelling:
                    lines.append("这个孩子喜欢通过故事学习，多用故事的框架来包装知识。")
                case LearningStyle.visual:
                    lines.append("多用画面感和比喻来描述事物。")
                case LearningStyle.questioning:
                    lines.append("多用提问引导，让孩子自己发现答案。")
                case LearningStyle.hands_on:
                    lines.append("多鼓励孩子动手尝试，给出可操作的小任务。")
        return "\n".join(lines)

    @staticmethod
    def _top_emotion(emotion_trend: dict) -> str:
        if not emotion_trend:
            return "平稳"
        return max(emotion_trend, key=emotion_trend.get)

    @staticmethod
    def compute_initial_snapshot(child_id: uuid.UUID) -> ProfileSnapshot:
        return ProfileSnapshot(
            child_id=child_id,
            vocabulary_level=VocabLevel.simple,
            curiosity_score=0.5,
            expression_score=0.5,
            reading_score=0.5,
            thinking_score=0.5,
            emotion_trend={"happy": 0.5, "curious": 0.3, "neutral": 0.2},
            learning_style=LearningStyle.storytelling,
        )

    @classmethod
    def facts_to_interests(cls, child_id: uuid.UUID, facts: list[dict]) -> list[InterestModel]:
        """Convert Memory Agent extracted facts (type=interest) to InterestModel records."""
        interests: list[InterestModel] = []
        for item in facts:
            if item.get("type") != "interest":
                continue
            topic = cls._infer_topic(item.get("fact", ""))
            if topic:
                interests.append(InterestModel(
                    child_id=child_id,
                    topic=topic,
                    weight=item.get("importance", 0.5),
                    trend=InterestTrend.rising,
                    source=InterestSource.implicit_clue,
                ))
        return interests

    TOPIC_KEYWORDS: dict[str, list[str]] = {
        "恐龙": ["恐龙", "霸王龙", "三角龙", "翼龙", "腕龙", "化石"],
        "太空": ["太空", "宇宙", "星球", "火箭", "宇航员", "火星", "月球", "太阳系"],
        "海洋": ["海洋", "大海", "鲨鱼", "鲸鱼", "海豚", "海底", "珊瑚"],
        "动物": ["动物", "小狗", "小猫", "熊猫", "老虎", "狮子", "大象"],
        "植物": ["植物", "花", "树", "种子", "森林", "花园"],
        "科学": ["实验", "科学", "化学", "物理", "发明", "机器人"],
        "绘画": ["画画", "绘画", "颜色", "画笔", "涂鸦", "画了"],
        "音乐": ["音乐", "唱歌", "钢琴", "吉他", "乐器", "节奏"],
        "运动": ["跑步", "足球", "篮球", "游泳", "运动", "跳绳"],
        "数学": ["数字", "计算", "数学", "几何", "加减"],
    }

    @classmethod
    def _infer_topic(cls, fact_text: str) -> str | None:
        """Infer topic from a fact string using keyword mapping."""
        text_lower = fact_text.lower()
        best_topic, best_score = None, 0
        for topic, keywords in cls.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_topic, best_score = topic, score
        return best_topic if best_score > 0 else None
