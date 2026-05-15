"""Simple LLM-backed text tagger built on LangChain structured output."""

from __future__ import annotations

import os
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class Tags(BaseModel):
    """Structured tags extracted from a piece of text."""

    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall sentiment of the text."
    )
    language: str = Field(
        description="ISO 639-1 code of the dominant language (e.g. 'en', 'es')."
    )
    aggressiveness: int = Field(
        description="How aggressive the text is on a 1-5 scale.",
        ge=1,
        le=5,
    )
    topics: list[str] = Field(
        description="Short topic tags (lowercase, 1-3 words each), at most 5.",
        max_length=5,
    )


_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Extract the requested tags from the passage. "
            "Only use the fields described in the schema.",
        ),
        ("human", "{text}"),
    ]
)


class Tagger:
    """Wraps a Claude model with a structured-output tagging schema."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        model = model or os.getenv("TAG_MODEL", "claude-sonnet-4-5-20250929")
        llm = ChatAnthropic(model=model, temperature=temperature)
        self._chain = _PROMPT | llm.with_structured_output(Tags)

    def tag(self, text: str) -> Tags:
        return self._chain.invoke({"text": text})
