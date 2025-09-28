"""Entrypoint for launching the Slack bot."""

from __future__ import annotations

import logging

from .config import get_settings
from .slack_app import create_app, run_socket_mode

logger = logging.getLogger(__name__)


def run() -> None:
    """CLI entrypoint that launches the Slack bot."""

    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")

    settings = get_settings()
    app = create_app(settings)

    if settings.slack_app_token:
        logger.info("Starting Slack bot in Socket Mode")
        run_socket_mode(app, settings)
    else:
        logger.info("Starting Slack bot via HTTP (requires external web server)")
        app.start(port=3000)


if __name__ == "__main__":
    run()
