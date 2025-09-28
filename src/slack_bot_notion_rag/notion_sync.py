"""Utilities for synchronising Notion content into the vector store."""

from __future__ import annotations

import logging
from typing import Iterable, List

import httpx
from notion_client import Client

from .config import Settings
from .rag_pipeline.vector_store import VectorStore

logger = logging.getLogger(__name__)


class NotionSyncService:
    """Fetch documents from Notion and push them into the vector store."""

    def __init__(self, settings: Settings, store: VectorStore | None = None) -> None:
        self._settings = settings
        self._store = store or VectorStore()
        self._client = Client(auth=settings.notion_api_token, client=build_http_client())

    def sync(self) -> None:
        """Pull configured databases and push contents into the vector store."""

        if not self._settings.notion_database_ids:
            logger.warning("No Notion databases configured; skipping sync")
            return

        documents: List[str] = []
        for database_id in self._settings.notion_database_ids:
            documents.extend(self.fetch_database_text(database_id))

        if not documents:
            logger.info("No documents retrieved from Notion")
            return

        self._store.ingest(documents)
        logger.info("Ingested %s documents into vector store", len(documents))

    def fetch_database_text(self, database_id: str) -> List[str]:
        """Return plain-text representation of the database entries."""

        logger.debug("Fetching Notion database: %s", database_id)
        # TODO: implement actual pagination and text extraction.
        return [f"Fetched page from Notion database {database_id}"]


def build_http_client() -> httpx.Client:
    """Return configured HTTP client for Notion SDK."""

    return httpx.Client(timeout=httpx.Timeout(30.0))


def bootstrap(settings: Settings) -> None:
    """High-level function to run a one-off Notion sync."""

    service = NotionSyncService(settings=settings)
    service.sync()
