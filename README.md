# Slack Bot Notion RAG

Lab knowledge-assistant Slack bot that retrieves answers from Notion content using Retrieval-Augmented Generation (RAG).

## Features (planned)
- Slack mention trigger and threaded replies with cited Notion sources
- RAG pipeline powered by LangChain and Chroma vector store
- Periodic Notion sync to keep embeddings fresh
- Configuration through environment variables and `.env` files

## Getting Started

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager (>=0.2 recommended)
- Slack App credentials (Bot token and Signing secret)
- Notion integration token and accessible databases
- OpenAI API key (or compatible LLM provider)

### Environment Setup (uv)
```bash
# 1. Install uv if not available yet
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. From the project root, create and populate the virtual environment
./scripts/setup_with_uv.sh

# 3. Activate the environment for your shell session
source .venv/bin/activate
```

The helper script runs `uv venv` and `uv pip install -e .[dev]` so tooling and dependencies stay in sync with `pyproject.toml`.

### Local Development
```bash
# Format and lint
uv run ruff check src tests
uv run black src tests

# Run tests
uv run pytest

# Start the bot (after configuring environment variables)
uv run python -m slack_bot_notion_rag.main
```

When using `uv run`, the command executes inside the managed virtual environment without manually activating it.

## Repository Layout
```
src/
  slack_bot_notion_rag/
    __init__.py
    config.py
    main.py
    slack_app.py
    notion_sync.py
    rag_pipeline/
      __init__.py
      retriever.py
      vector_store.py
      llm.py
scripts/
  bootstrap_vectors.py
  setup_with_uv.sh
```

## Next Steps
- Implement credential loading and secrets management integrations
- Add Notion ingestion workflows and persistence layer
- Harden Slack event handling and message formatting
- Set up CI and deployment automations (Cloud Run / AWS Lambda)
