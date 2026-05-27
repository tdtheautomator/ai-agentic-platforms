"""Semantic memory management (ChromaDB)."""

import uuid
from pathlib import Path
from typing import Optional


class SemanticMemory:
    """Semantic memory backed by ChromaDB."""

    def __init__(self, chroma_dir: Path):
        """
        Initialize semantic memory.
        
        Args:
            chroma_dir: Path to ChromaDB directory
        """
        self.chroma_dir = chroma_dir
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None
        self._embedder = None
        self._ready = False
        self._init_chroma()

    def _init_chroma(self) -> None:
        """Initialize ChromaDB."""
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            self._client = chromadb.PersistentClient(path=str(self.chroma_dir))
            self._collection = self._client.get_or_create_collection(
                "ecommerce_kb", metadata={"hnsw:space": "cosine"}
            )
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            self._ready = True
            print("[E-Commerce] ChromaDB ready")
        except Exception as e:
            print(f"[E-Commerce] ChromaDB init failed: {e}")

    def is_ready(self) -> bool:
        """Check if semantic memory is ready."""
        return self._ready

    def add(self, text: str, meta: Optional[dict] = None) -> None:
        """
        Add text to semantic memory.
        
        Args:
            text: Text to add
            meta: Metadata
        """
        if not self._ready:
            return
        emb = self._embedder.encode([text]).tolist()
        self._collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=emb,
            documents=[text],
            metadatas=[meta or {}],
        )

    def query(self, query: str, top_k: int = 2) -> list[str]:
        """
        Query semantic memory.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of matching documents
        """
        if not self._ready or self._collection.count() == 0:
            return []
        emb = self._embedder.encode([query]).tolist()
        res = self._collection.query(
            query_embeddings=emb, n_results=min(top_k, self._collection.count())
        )
        return res["documents"][0]

    def count(self) -> int:
        """Get number of items in collection."""
        if not self._ready:
            return 0
        return self._collection.count()
