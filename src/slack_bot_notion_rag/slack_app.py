"""Slack Bolt app factory and handlers."""

from __future__ import annotations

import logging
import re
from typing import Callable

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import Settings
from .rag_pipeline.llm import LLMService
from .rag_pipeline.retriever import Retriever
from .rag_pipeline.vector_store import VectorStore

logger = logging.getLogger(__name__)

MENTION_PATTERN = re.compile(r"<@([A-Z0-9]+)>")


def create_app(settings: Settings) -> App:
    """Create a Slack Bolt app with event handling backed by the RAG pipeline."""

    app = App(token=settings.slack_bot_token, signing_secret=settings.slack_signing_secret)

    vector_store = VectorStore.from_settings(settings)
    retriever = Retriever(vector_store, default_k=settings.retriever_top_k)
    llm_service = LLMService(settings)

    @app.event("app_mention")
    def handle_mention(body: dict, say: Callable[..., None]) -> None:
        """Respond to mentions by delegating to the RAG pipeline."""

        event = body.get("event", {})
        user_question = clean_user_question(event.get("text", ""))
        channel = event.get("channel")
        thread_ts = event.get("thread_ts") or event.get("ts")

        logger.info("Received mention in channel=%s thread=%s", channel, thread_ts)

        if not user_question.strip():
            say(
                text="すみません、質問の内容が読み取れませんでした。もう一度お願いします。",
                thread_ts=thread_ts,
            )
            return

        try:
            context_documents = retriever.retrieve(user_question)
            response = llm_service.answer(user_question, context_documents)
            say(text=response.render_with_citations(), thread_ts=thread_ts)
        except Exception as exc:  # pragma: no cover - guardrail for runtime failures
            logger.exception("Failed to generate answer: %s", exc)
            say(
                text="内部エラーが発生しました。しばらくしてからもう一度お試しください。",
                thread_ts=thread_ts,
            )

    return app


def clean_user_question(text: str) -> str:
    """Remove bot mention tokens and trim whitespace."""

    return MENTION_PATTERN.sub("", text or "").strip()


def run_socket_mode(app: App, settings: Settings) -> None:
    """Run the Slack app in Socket Mode if app-level token provided."""

    if not settings.slack_app_token:
        raise RuntimeError("SLACK_APP_TOKEN is not configured for Socket Mode")

    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()
