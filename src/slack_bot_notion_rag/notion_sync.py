"""Utilities for synchronising Notion content into the vector store."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List

import httpx
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from notion_client import Client
from notion_client.errors import APIResponseError

from .config import Settings
from .rag_pipeline.vector_store import VectorStore

logger = logging.getLogger(__name__)


class NotionSyncService:
    """Fetch documents from Notion and push them into the vector store."""

    def __init__(
        self,
        settings: Settings,
        store: VectorStore | None = None,
        *,
        text_splitter: RecursiveCharacterTextSplitter | None = None,
    ) -> None:
        self._settings = settings
        self._store = store or VectorStore.from_settings(settings)
        self._client = Client(auth=settings.notion_api_token, client=build_http_client(settings))
        self._splitter = text_splitter or RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    def sync(self) -> None:
        """Pull configured databases and push contents into the vector store."""

        if not self._settings.notion_root_page_ids:
            logger.warning("No Notion root pages configured; skipping sync")
            return

        for root_page_id in self._settings.notion_root_page_ids:
            try:
                documents = self._fetch_documents_for_root_page(root_page_id)
            except Exception as exc:  # pragma: no cover - defensive catch for API failures
                logger.exception("Failed to fetch Notion hierarchy %s: %s", root_page_id, exc)
                continue

            if not documents:
                logger.info("No documents retrieved from Notion root page %s", root_page_id)
                continue

            logger.info(
                "Replacing %s documents in vector store for root page %s",
                len(documents),
                root_page_id,
            )
            self._store.delete_where(filter={"root_page_id": root_page_id})
            self._store.add_documents(documents)

    def _fetch_documents_for_root_page(self, root_page_id: str) -> List[Document]:
        seen_pages: set[str] = set()
        seen_databases: set[str] = set()
        return self._process_page(
            page_id=root_page_id,
            root_page_id=root_page_id,
            seen_pages=seen_pages,
            seen_databases=seen_databases,
        )

    def _process_page(
        self,
        *,
        page_id: str,
        root_page_id: str,
        seen_pages: set[str],
        seen_databases: set[str],
        database_id: str | None = None,
    ) -> List[Document]:
        if page_id in seen_pages:
            return []
        seen_pages.add(page_id)

        documents: List[Document] = []
        documents.extend(
            self._build_documents_for_page(
                page_id=page_id,
                root_page_id=root_page_id,
                database_id=database_id,
            )
        )

        for resource in self._discover_child_resources(page_id):
            resource_id = resource.get("id")
            if not resource_id:
                continue
            resource_type = resource.get("type")
            if resource_type == "page":
                documents.extend(
                    self._process_page(
                        page_id=resource_id,
                        root_page_id=root_page_id,
                        seen_pages=seen_pages,
                        seen_databases=seen_databases,
                        database_id=None,
                    )
                )
            elif resource_type == "database":
                documents.extend(
                    self._process_database(
                        database_id=resource_id,
                        root_page_id=root_page_id,
                        seen_pages=seen_pages,
                        seen_databases=seen_databases,
                    )
                )

        return documents

    def _build_documents_for_page(
        self,
        page_id: str,
        *,
        root_page_id: str,
        database_id: str | None = None,
    ) -> List[Document]:
        try:
            page = self._client.pages.retrieve(page_id=page_id)
        except Exception as exc:  # pragma: no cover - defensive catch for API failures
            logger.warning("Failed retrieving page %s: %s", page_id, exc)
            return []

        page_title = extract_title_from_properties(page.get("properties", {})) or page.get("url", "")
        page_url = page.get("url")
        content = self._fetch_page_content(page_id)
        if not content.strip():
            return []

        source_type = "database_page" if database_id else "page"
        base_document = Document(
            page_content=content,
            metadata={
                "title": page_title or "Untitled",
                "source": page_url,
                "page_id": page_id,
                "root_page_id": root_page_id,
                "source_type": source_type,
                **({"database_id": database_id} if database_id else {}),
            },
        )
        chunks = self._splitter.split_documents([base_document])
        return self._attach_chunk_ids(page_id, chunks)

    def _discover_child_resources(self, block_id: str) -> Iterable[Dict]:
        start_cursor = None
        while True:
            response = self._client.blocks.children.list(block_id=block_id, start_cursor=start_cursor)
            for block in response.get("results", []):
                block_type = block.get("type")
                child_id = block.get("id")
                if block_type == "child_page" and child_id:
                    yield {"type": "page", "id": child_id}
                    continue
                if block_type == "child_database" and child_id:
                    yield {"type": "database", "id": child_id}
                    continue
                if block.get("has_children") and child_id:
                    yield from self._discover_child_resources(child_id)
            if not response.get("has_more"):
                break
            start_cursor = response.get("next_cursor")

    def _process_database(
        self,
        *,
        database_id: str,
        root_page_id: str,
        seen_pages: set[str],
        seen_databases: set[str],
    ) -> List[Document]:
        if database_id in seen_databases:
            return []
        seen_databases.add(database_id)

        try:
            pages = list(self._iterate_database_pages(database_id))
        except APIResponseError as exc:
            if self._should_skip_inaccessible_database(exc):
                logger.warning(
                    "Skipping Notion database %s due to inaccessible data sources: %s",
                    database_id,
                    exc,
                )
                return []
            raise

        documents: List[Document] = []
        for page in pages:
            page_id = page.get("id")
            if not page_id:
                continue
            documents.extend(
                self._process_page(
                    page_id=page_id,
                    root_page_id=root_page_id,
                    seen_pages=seen_pages,
                    seen_databases=seen_databases,
                    database_id=database_id,
                )
            )
        return documents

    def _should_skip_inaccessible_database(self, error: APIResponseError) -> bool:
        """Return True when the integration cannot access the database content."""

        message = getattr(error, "message", str(error))
        if message and "does not contain any data sources accessible" in message:
            return True
        code = getattr(error, "code", None)
        return code in {"restricted_resource", "object_not_found"}

    def _attach_chunk_ids(self, page_id: str, chunks: Iterable[Document]) -> List[Document]:
        page_prefix = page_id.replace("-", "")
        enriched: List[Document] = []
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{page_prefix}:{index}"
            enriched.append(chunk)
        return enriched

    def _iterate_database_pages(self, database_id: str) -> Iterable[Dict]:
        start_cursor = None
        while True:
            response = self._client.databases.query(
                database_id=database_id,
                start_cursor=start_cursor,
                page_size=self._settings.notion_page_size,
            )
            results = response.get("results", [])
            for page in results:
                yield page
            if not response.get("has_more"):
                break
            start_cursor = response.get("next_cursor")

    def _fetch_page_content(self, page_id: str) -> str:
        blocks = list(self._collect_blocks(page_id))
        lines: List[str] = []
        for block in blocks:
            lines.extend(render_block(block))
        return "\n".join(line for line in lines if line)

    def _collect_blocks(self, block_id: str) -> Iterable[Dict]:
        start_cursor = None
        while True:
            response = self._client.blocks.children.list(block_id=block_id, start_cursor=start_cursor)
            for block in response.get("results", []):
                yield block
                child_id = block.get("id")
                block_type = block.get("type")
                if (
                    block.get("has_children")
                    and child_id
                    and block_type not in {"child_page", "child_database"}
                ):
                    yield from self._collect_blocks(child_id)
            if not response.get("has_more"):
                break
            start_cursor = response.get("next_cursor")

    def fetch_database_text(self, database_id: str, *, root_page_id: str | None = None) -> List[str]:
        """Return plain-text representation of the database entries (backwards compatibility)."""

        docs = self._process_database(
            database_id=database_id,
            root_page_id=root_page_id or database_id,
            seen_pages=set(),
            seen_databases=set(),
        )
        return [doc.page_content for doc in docs]


def build_http_client(settings: Settings) -> httpx.Client:
    """Return configured HTTP client for Notion SDK."""

    timeout = httpx.Timeout(settings.notion_request_timeout)
    return httpx.Client(timeout=timeout)


def extract_title_from_properties(properties: Dict) -> str | None:
    """Return the first title property from a Notion page."""

    for prop in properties.values():
        if prop.get("type") == "title":
            rich_text = prop.get("title", [])
            return "".join(fragment.get("plain_text", "") for fragment in rich_text).strip() or None
    return None


def render_block(block: Dict) -> List[str]:
    """Convert a Notion block to a list of plain-text lines."""

    block_type = block.get("type")
    value = block.get(block_type, {}) if block_type else {}
    rich_text = value.get("rich_text", [])
    content = "".join(fragment.get("plain_text", "") for fragment in rich_text).strip()

    if not content:
        return []

    if block_type in {"heading_1", "heading_2", "heading_3"}:
        hashes = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}.get(block_type, "")
        return [f"{hashes} {content}".strip()]
    if block_type == "bulleted_list_item":
        return [f"- {content}"]
    if block_type == "numbered_list_item":
        return [f"1. {content}"]
    if block_type == "to_do":
        checked = value.get("checked", False)
        prefix = "[x]" if checked else "[ ]"
        return [f"{prefix} {content}"]
    return [content]


def bootstrap(settings: Settings) -> None:
    """High-level function to run a one-off Notion sync."""

    service = NotionSyncService(settings=settings)
    service.sync()
