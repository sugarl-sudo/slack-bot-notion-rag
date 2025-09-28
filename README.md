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
- Slack App credentials (Bot token and Signing secret)
- Notion integration token and accessible databases
- OpenAI API key (or compatible LLM provider)

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
```

Create a `.env` file (see `.env.example`) with your credentials before running the bot.

### Local Development
```bash
# Format and lint
ruff check src tests
black src tests

# Run tests
pytest

# Start the bot (after configuring environment variables)
python -m slack_bot_notion_rag.main
```

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
```

## Next Steps
- Implement credential loading and secrets management integrations
- Add Notion ingestion workflows and persistence layer
- Harden Slack event handling and message formatting
- Set up CI and deployment automations (Cloud Run / AWS Lambda)
