"""
Semantic memory store for banking-demo using ChromaDB.

Stores banking rules and decision patterns as vectors for similarity search.
Uses sentence-transformers for embeddings. Implements the MemoryStore interface.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import structlog

from memory.base import MemoryStore

logger = structlog.get_logger(__name__)


class SemanticMemory(MemoryStore):
    """
    Semantic memory using ChromaDB vector store.
    
    Stores banking rules and decision patterns as embeddings for
    similarity-based retrieval. Lazily initializes ChromaDB and
    sentence-transformers on first use.
    
    Attributes:
        chroma_dir: Path to ChromaDB persistent storage.
        client: ChromaDB client (lazy-loaded).
        collection: ChromaDB collection (lazy-loaded).
        embedder: Sentence transformer model (lazy-loaded).
        ready: Flag indicating if semantic memory is initialized.
    """

    def __init__(self, chroma_dir: str | Path = "/data/chroma"):
        """
        Initialize semantic memory.
        
        Args:
            chroma_dir: Path to ChromaDB directory (default: /data/chroma).
        """
        self.chroma_dir = Path(chroma_dir)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)

        self.client = None
        self.collection = None
        self.embedder = None
        self.ready = False

    @property
    def store_name(self) -> str:
        """Get store name."""
        return "semantic"

    async def _initialize(self) -> None:
        """
        Lazily initialize ChromaDB and sentence-transformers.
        
        Called on first use to avoid startup overhead if semantic
        memory is not needed.
        """
        if self.ready:
            return

        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            self.client = chromadb.PersistentClient(path=str(self.chroma_dir))
            self.collection = self.client.get_or_create_collection(
                "banking_knowledge",
                metadata={"hnsw:space": "cosine"},
            )
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            self.ready = True

            await logger.ainfo("semantic_memory_initialized")

        except ImportError as exc:
            await logger.awarning(
                "semantic_memory_init_failed",
                error="ChromaDB or sentence-transformers not installed",
            )
            self.ready = False
            raise

        except Exception as exc:
            await logger.aerror(
                "semantic_memory_init_failed",
                error=str(exc),
            )
            raise

    async def add(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a document to semantic memory.
        
        Args:
            key: Unique document ID (default: generated UUID).
            value: Document text to embed.
            metadata: Optional metadata (source, type, etc.).
        """
        if not self.ready:
            await self._initialize()

        try:
            doc_id = key or str(uuid.uuid4())
            embedding = self.embedder.encode([str(value)]).tolist()

            self.collection.add(
                ids=[doc_id],
                embeddings=embedding,
                documents=[str(value)],
                metadatas=[metadata or {}],
            )

            await logger.ainfo(
                "semantic_memory_add",
                doc_id=doc_id,
                doc_len=len(str(value)),
            )

        except Exception as exc:
            await logger.aerror(
                "semantic_memory_add_failed",
                error=str(exc),
            )
            raise

    async def get(self, key: str) -> Any | None:
        """
        Get a document by ID.
        
        Args:
            key: Document ID.
            
        Returns:
            Document text, or None if not found.
        """
        if not self.ready:
            await self._initialize()

        try:
            result = self.collection.get(ids=[key])
            if result["documents"]:
                return result["documents"][0]
            return None

        except Exception as exc:
            await logger.aerror(
                "semantic_memory_get_failed",
                error=str(exc),
            )
            raise

    async def search(
        self,
        query: str,
        top_k: int = 2,
    ) -> list[Any]:
        """
        Search semantic memory using vector similarity.
        
        Args:
            query: Query text to search for.
            top_k: Maximum number of results.
            
        Returns:
            List of matching document texts.
        """
        if not self.ready:
            await self._initialize()

        try:
            if self.collection.count() == 0:
                return []

            query_embedding = self.embedder.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(top_k, self.collection.count()),
            )

            await logger.ainfo(
                "semantic_memory_search",
                query_len=len(query),
                results=len(results["documents"][0]),
            )

            return results["documents"][0]

        except Exception as exc:
            await logger.aerror(
                "semantic_memory_search_failed",
                error=str(exc),
            )
            raise

    async def clear(self) -> None:
        """Clear all documents from semantic memory."""
        if not self.ready:
            await self._initialize()

        try:
            # Delete and recreate collection
            self.client.delete_collection("banking_knowledge")
            self.collection = self.client.get_or_create_collection(
                "banking_knowledge",
                metadata={"hnsw:space": "cosine"},
            )

            await logger.ainfo("semantic_memory_cleared")

        except Exception as exc:
            await logger.aerror(
                "semantic_memory_clear_failed",
                error=str(exc),
            )
            raise

    async def count(self) -> int:
        """Get the number of documents in semantic memory."""
        if not self.ready:
            await self._initialize()

        try:
            return self.collection.count()

        except Exception as exc:
            await logger.aerror(
                "semantic_memory_count_failed",
                error=str(exc),
            )
            return 0
