# Architecture Overview

## Components
- Slack App (Bolt) handles events and routes questions to the RAG pipeline.
- Notion Sync Service fetches content from configured Notion root pages (including all descendant pages and database entries), chunks it, and writes embeddings to the vector store.
- Vector Store (Chroma) persists embedded document fragments for similarity search.
- LLM module (OpenAI Chat model via LangChain) crafts answers and returns Slack-ready text with citations.

## Control Flow
1. User mentions the bot in Slack.
2. Slack handler cleans the question text and retrieves relevant chunks from the vector store.
3. Retriever queries Chroma for semantically similar documents using OpenAI embeddings.
4. LLM generates an answer combining the question and retrieved context, referencing chunks with `[n]` markers.
5. Bot posts the answer in the originating Slack thread with a citation list linking back to Notion.

## Background Sync
- A scheduled job or manual trigger runs `uv run python scripts/bootstrap_vectors.py`.
- The sync service pulls the entire hierarchy beneath each configured Notion parent page, flattens block content, and splits it into overlapping chunks.
- Chroma embeddings are regenerated per root page to keep the knowledge base fresh.

## Configuration
- All secrets are read from environment variables (see `.env.example`).
- Pydantic settings object ensures validation, chunking defaults, and API tuning parameters.
- Development environment provisioning uses `uv` (see `README.md` for instructions).

## Deployment Targets
- Designed for containerized deployment on Google Cloud Run.
- Slack HTTP mode requires HTTPS endpoint; Socket Mode works for local development.
- Supporting GCP services: Cloud Scheduler triggers a Cloud Functions job that refreshes the Notion vector store on a schedule, and Secret Manager holds credentials for Slack, Notion, and LLM providers.
