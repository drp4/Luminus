"""LLM factory — supports multiple providers via config switch."""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from config import settings


def create_llm(temperature: float = 0.7, max_tokens: int = 1024):
    """Create an LLM instance based on LLM_PROVIDER config.

    Provider options:
      - "openai":    OpenAI-compatible API (DeepSeek, OpenAI, etc.)
      - "anthropic": Anthropic-compatible API (Claude, DeepSeek Anthropic endpoint)
    """
    provider = settings.llm_provider

    if provider == "anthropic":
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Default: OpenAI-compatible
    return ChatOpenAI(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        base_url=settings.anthropic_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )
