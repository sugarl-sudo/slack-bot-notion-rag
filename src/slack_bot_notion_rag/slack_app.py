"""Slack Bolt app factory and handlers."""

from __future__ import annotations

import logging
from typing import Callable

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import Settings
from .rag_pipeline import retriever
from .rag_pipeline.llm import generate_answer

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> App:
    """Create a Slack Bolt app with placeholder event handling."""

    app = App(token=settings.slack_bot_token, signing_secret=settings.slack_signing_secret)

    @app.event("app_mention")
    def handle_mention(body: dict, say: Callable[..., None]) -> None:
        """Respond to mentions by delegating to the RAG pipeline."""

        user_question = body.get("event", {}).get("text", "")
        channel = body.get("event", {}).get("channel")
        thread_ts = body.get("event", {}).get("ts")

        logger.info("Received mention in channel=%s thread=%s", channel, thread_ts)

        if not user_question:
            say(text="すみません、質問の内容が読み取れませんでした。もう一度お願いします。", thread_ts=thread_ts)
            return

        context_chunks = retriever.retrieve_context(user_question)
        response = generate_answer(user_question, context_chunks)

        say(text=response.text, thread_ts=thread_ts)

    return app


def run_socket_mode(app: App, settings: Settings) -> None:
    """Run the Slack app in Socket Mode if app-level token provided."""

    if not settings.slack_app_token:
        raise RuntimeError("SLACK_APP_TOKEN is not configured for Socket Mode")

    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()
