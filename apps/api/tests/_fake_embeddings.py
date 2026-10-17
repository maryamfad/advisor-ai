"""Deterministic fake embeddings for tests that exercise RAG ingestion
and search (app/services/policy_document_ingestion.py) without a real
OPENAI_API_KEY or network call -- same idea as _fake_chat_model.py's
ScriptedChatModel, but for embeddings: a bag-of-hashed-words vector is
"good enough" to prove client isolation and basic retrieval
correctness without needing real semantic embeddings.
"""

from langchain_core.embeddings import Embeddings

EMBEDDING_DIMENSIONS = 16


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    @staticmethod
    def _embed(text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        for word in text.lower().split():
            vector[hash(word) % EMBEDDING_DIMENSIONS] += 1.0
        return vector
