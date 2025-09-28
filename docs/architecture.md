# Architecture Overview

## Components
- Slack App (Bolt) handles events and routes questions to the RAG pipeline.
- Notion Sync Service fetches content from configured Notion databases and ingests it into the vector store.
- Vector Store (Chroma placeholder) stores embedded document chunks for similarity search.
- LLM module wraps calls to GPT-family models to craft responses with citations.

## Control Flow
1. User mentions the bot in Slack.
2. Slack handler extracts the question and requests relevant chunks from the retriever.
3. Retriever queries the vector store for semantically similar documents.
4. LLM generates an answer combining the question and retrieved context.
5. Bot posts the answer in the originating Slack thread with optional citations.

## Background Sync
- A scheduled job or manual trigger runs `scripts/bootstrap_vectors.py`.
- The sync service pulls Notion pages, cleans text, and stores embeddings.
- Vector store persists on disk (future work) for consistent retrieval at runtime.

## Configuration
- All secrets are read from environment variables (see `.env.example`).
- Pydantic settings object ensures validation and type coercion.
- Development environment provisioning uses `uv` (see `README.md` for instructions).

## Deployment Targets
- Designed for containerized deployment (Cloud Run, AWS Lambda with API Gateway, or similar).
- Slack HTTP mode requires HTTPS endpoint; Socket Mode works for local development.
