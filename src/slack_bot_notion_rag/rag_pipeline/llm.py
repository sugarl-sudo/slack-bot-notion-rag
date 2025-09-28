"""LLM-facing helper functions and response models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from langchain.docstore.document import Document
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..config import Settings, get_settings


@dataclass
class Citation:
    """Reference to a Notion page used in the answer."""

    label: str
    title: str
    url: str | None


@dataclass
class LLMResponse:
    """Structured representation of generated answer."""

    text: str
    citations: list[Citation]

    def render_with_citations(self) -> str:
        """Return Markdown-friendly string combining answer and references."""

        if not self.citations:
            return self.text

        citation_lines = []
        for citation in self.citations:
            if citation.url:
                citation_lines.append(f"{citation.label} <{citation.url}|{citation.title}>")
            else:
                citation_lines.append(f"{citation.label} {citation.title}")
        joined = "\n".join(citation_lines)
        return f"{self.text}\n\n参照:\n{joined}"


class LLMService:
    """Encapsulates prompt construction and LLM invocation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._llm = ChatOpenAI(
            model=self._settings.openai_model,
            api_key=self._settings.openai_api_key,
            base_url=self._settings.openai_api_base,
            temperature=self._settings.openai_temperature,
            max_tokens=self._settings.answer_max_tokens,
        )
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
あなたは研究室の Slack ボットです。以下のコンテキストからユーザーの質問に回答してください。
- コンテキストに含まれる情報のみを根拠として回答してください。
- 参照したコンテキストの識別子 ([1] など) を回答中に含めてください。
- 情報が不足している場合は、その旨を日本語で丁寧に伝えてください。
                    """.strip(),
                ),
                (
                    "human",
                    """
質問:
{question}

コンテキスト:
{context}
                    """.strip(),
                ),
            ]
        )

    def answer(self, question: str, documents: Sequence[Document]) -> LLMResponse:
        """Generate an answer from the provided context documents."""

        if not documents:
            text = "申し訳ありません。関連する情報を見つけられませんでした。Notion のデータに追加する場合は管理者にご連絡ください。"
            return LLMResponse(text=text, citations=[])

        context_text, citations = self._format_context(documents)
        messages = self._prompt.format_messages(question=question, context=context_text)
        raw_response = self._llm.invoke(messages)
        answer_text = getattr(raw_response, "content", str(raw_response))
        return LLMResponse(text=answer_text.strip(), citations=citations)

    def _format_context(self, documents: Sequence[Document]) -> tuple[str, list[Citation]]:
        parts: list[str] = []
        citations: list[Citation] = []

        for index, document in enumerate(documents, start=1):
            metadata = document.metadata or {}
            title = metadata.get("title") or "Untitled"
            url = metadata.get("source")
            label = f"[{index}]"
            citations.append(Citation(label=label, title=title, url=url))
            parts.append(f"{label} {title}\n{document.page_content}")

        return "\n\n".join(parts), citations


def generate_answer(question: str, documents: Sequence[Document], settings: Settings | None = None) -> LLMResponse:
    """Convenience wrapper mirroring the legacy function signature."""

    service = LLMService(settings=settings)
    return service.answer(question, documents)
