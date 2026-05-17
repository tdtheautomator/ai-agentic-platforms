"""
Semantic memory — ChromaDB vector embeddings for knowledge base.

Stores and queries IT knowledge base articles by semantic similarity.
"""

import uuid
from pathlib import Path

# Module-level state
_chroma_client = None
_chroma_col = None
_embedder = None
_chroma_ready: bool = False


def _init_chroma(chroma_dir: Path, collection_name: str = "it_knowledge") -> None:
    """Initialize ChromaDB client and collection."""
    global _chroma_client, _chroma_col, _embedder, _chroma_ready
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        _chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
        _chroma_col = _chroma_client.get_or_create_collection(
            collection_name, metadata={"hnsw:space": "cosine"})
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        _chroma_ready = True
        print("[IT Support] ChromaDB ready")
    except Exception as e:
        print(f"[IT Support] ChromaDB init failed: {e}")


def sem_add(text: str, meta: dict | None = None) -> None:
    """Add text embedding to knowledge base."""
    if not _chroma_ready:
        return
    emb = _embedder.encode([text]).tolist()
    _chroma_col.add(ids=[str(uuid.uuid4())], embeddings=emb,
                    documents=[text], metadatas=[meta or {}])


def sem_query(query: str, top_k: int = 2) -> list[str]:
    """Query knowledge base by semantic similarity."""
    if not _chroma_ready or _chroma_col.count() == 0:
        return []
    emb = _embedder.encode([query]).tolist()
    n = min(top_k, _chroma_col.count())
    res = _chroma_col.query(query_embeddings=emb, n_results=n)
    return res["documents"][0]
