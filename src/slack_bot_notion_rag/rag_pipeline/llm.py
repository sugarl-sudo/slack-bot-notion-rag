"""LLM-facing helper functions and response models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class LLMResponse:
    """Structured representation of generated answer."""

    text: str
    citations: list[str]


def generate_answer(question: str, context_chunks: Iterable[str]) -> LLMResponse:
    """Generate a placeholder response until LLM wiring is implemented."""

    context_summary = "\n".join(f"- {chunk}" for chunk in context_chunks)
    text = (
        "\n".join(
            [
                "開発中のためスタブ応答を返しています。",
                "以下のコンテキストを参照しました:",
                context_summary or "(まだデータが同期されていません)",
            ]
        )
    )
    return LLMResponse(text=text, citations=[])
