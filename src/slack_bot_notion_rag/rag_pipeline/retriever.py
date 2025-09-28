"""Retriever built on top of the shared vector store."""

from __future__ import annotations

from typing import List, Sequence

from langchain.docstore.document import Document

from ..config import Settings, get_settings
from .vector_store import VectorStore


class Retriever:
    """Facade used to obtain RAG context from the vector store."""

    def __init__(self, store: VectorStore, *, default_k: int) -> None:
        self._store = store
        self._default_k = default_k

    def retrieve(self, query: str, *, limit: int | None = None) -> List[Document]:
        """Return textual chunks best matching the query."""

        top_k = limit or self._default_k
        return self._store.similarity_search(query, limit=top_k)


def build_retriever(settings: Settings | None = None) -> Retriever:
    """Construct a retriever for the provided settings (defaults to global)."""

    settings = settings or get_settings()
    store = VectorStore.from_settings(settings)
    return Retriever(store, default_k=settings.retriever_top_k)


def retrieve_context(query: str, *, limit: int | None = None) -> List[Document]:
    """Convenience global retriever for scripts and REPL usage."""

    retriever = build_retriever()
    return retriever.retrieve(query, limit=limit)


class RetrievedContext:
    """Container for retrieved chunks that can be passed to LLMs."""

    def __init__(self, chunks: Sequence[Document]):
        self.chunks = list(chunks)

    def as_prompt(self) -> str:
        """Render the chunks for injection into an LLM prompt."""

        formatted = []
        for index, document in enumerate(self.chunks, start=1):
            label = f"[{index}]"
            title = document.metadata.get("title") or "Untitled"
            formatted.append(f"{label} {title}\n{document.page_content}")
        return "\n\n".join(formatted)
