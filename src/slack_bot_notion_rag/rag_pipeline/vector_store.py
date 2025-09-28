"""Chroma-based vector store management layer."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from langchain.docstore.document import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from ..config import Settings


class VectorStore:
    """Wrapper around a persistent Chroma collection."""

    def __init__(
        self,
        *,
        persist_directory: Path,
        collection_name: str,
        embedding_model: str,
        openai_api_key: str,
        openai_api_base: str | None = None,
    ) -> None:
        self._persist_directory = persist_directory
        self._persist_directory.mkdir(parents=True, exist_ok=True)
        self._collection_name = collection_name
        self._embedding = OpenAIEmbeddings(
            model=embedding_model,
            api_key=openai_api_key,
            base_url=openai_api_base,
        )
        self._store: Chroma | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "VectorStore":
        return cls(
            persist_directory=Path(settings.vector_store_path),
            collection_name=settings.vector_collection_name,
            embedding_model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_api_base,
        )

    def _get_store(self) -> Chroma:
        if self._store is None:
            self._store = Chroma(
                collection_name=self._collection_name,
                persist_directory=str(self._persist_directory),
                embedding_function=self._embedding,
            )
        return self._store

    def similarity_search(self, query: str, *, limit: int) -> list[Document]:
        """Return the most similar documents for the provided query."""

        store = self._get_store()
        return store.similarity_search(query, k=limit)

    def upsert(self, documents: Sequence[Document]) -> None:
        """Insert or replace documents in the collection."""

        if not documents:
            return

        store = self._get_store()
        chunk_ids = [doc.metadata.get("chunk_id") for doc in documents]
        ids_to_remove = [chunk_id for chunk_id in chunk_ids if chunk_id]
        if ids_to_remove:
            store.delete(ids=ids_to_remove)

        store.add_documents(documents=documents, ids=[chunk_id or None for chunk_id in chunk_ids])
        store.persist()

    def delete_where(self, *, filter: dict[str, str]) -> None:
        """Delete all documents matching the metadata filter."""

        if not filter:
            return
        store = self._get_store()
        store.delete(where=filter)
        store.persist()

    def reset(self) -> None:
        """Remove all documents from the collection."""

        store = self._get_store()
        store.delete()
        store.persist()

    def add_documents(self, documents: Iterable[Document]) -> None:
        """Convenience wrapper to add documents without de-duplication."""

        docs = list(documents)
        if not docs:
            return
        store = self._get_store()
        store.add_documents(documents=docs)
        store.persist()
