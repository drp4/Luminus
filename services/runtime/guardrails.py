from __future__ import annotations


class Guardrails:
    """Input/output content filters. Decorator-compatible.

    Currently: simple keyword-based filtering.
    Future: LLM-based moderation, PII detection, age-appropriateness scoring.
    """

    SENSITIVE_KEYWORDS = [
        # Placeholder — replace with actual child safety keyword list
    ]

    @classmethod
    def filter_input(cls, text: str) -> str:
        for kw in cls.SENSITIVE_KEYWORDS:
            text = text.replace(kw, "***")
        return text

    @classmethod
    def filter_output(cls, text: str) -> str:
        for kw in cls.SENSITIVE_KEYWORDS:
            text = text.replace(kw, "***")
        return text
