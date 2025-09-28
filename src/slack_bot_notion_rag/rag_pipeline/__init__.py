"""RAG pipeline components for Slack bot."""

from .retriever import Retriever, retrieve_context

__all__ = ["Retriever", "retrieve_context"]
