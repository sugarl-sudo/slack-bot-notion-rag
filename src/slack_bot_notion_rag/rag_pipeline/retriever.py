"""Retriever stub that will wrap the vector store."""

from __future__ import annotations

from typing import Iterable, List

from .vector_store import VectorStore


class Retriever:
    """Facade used by Slack handlers to obtain RAG context."""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def retrieve(self, query: str, *, limit: int = 4) -> List[str]:
        """Return textual chunks best matching the query."""

        return list(self._store.similarity_search(query, limit=limit))


_default_store = VectorStore()
_default_retriever = Retriever(_default_store)


def retrieve_context(query: str, *, limit: int = 4) -> List[str]:
    """Module-level helper that proxies to the default retriever."""

    return _default_retriever.retrieve(query, limit=limit)


class RetrievedContext:
    """Container for retrieved chunks that can be passed to LLMs."""

    def __init__(self, chunks: Iterable[str]):
        self.chunks = list(chunks)

    def as_prompt(self) -> str:
        """Render the chunks for injection into an LLM prompt."""

        return "\n\n".join(self.chunks)
