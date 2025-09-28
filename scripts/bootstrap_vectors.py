"""CLI helper to run initial Notion sync."""

from __future__ import annotations

import logging

from slack_bot_notion_rag.config import get_settings
from slack_bot_notion_rag.notion_sync import bootstrap


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    bootstrap(settings)


if __name__ == "__main__":
    main()
