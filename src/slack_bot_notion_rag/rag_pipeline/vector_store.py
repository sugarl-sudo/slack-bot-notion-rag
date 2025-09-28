"""Thin wrapper around the vector store technology (placeholder implementation)."""

from __future__ import annotations

from typing import Iterable, List


class VectorStore:
    """In-memory stub to help wire up the architecture."""

    def __init__(self) -> None:
        self._documents: List[str] = [
            "Notionドキュメントの連携は現在準備中です。",
            "このメッセージはテスト用のスタブです。",
        ]

    def load(self) -> None:
        """Load or initialize the vector store (to be replaced with Chroma)."""

        # TODO: implement persistence-backed store.

    def ingest(self, documents: Iterable[str]) -> None:
        """Add documents to the vector store."""

        self._documents.extend(documents)

    def similarity_search(self, query: str, *, limit: int = 4) -> Iterable[str]:
        """Return placeholder results until embeddings are wired up."""

        del query  # placeholder to silence unused variable warnings
        yield from self._documents[:limit]
