import logging
from typing import Any

from app.config import (
    CHROMA_COLLECTION,
    CHROMA_PERSIST_DIR,
    EMBEDDING_API_KEY,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
)

logger = logging.getLogger(__name__)

_collection = None
_embed_fn = None


def _get_embedding(text: str) -> list[float]:
    """Upstage embedding API 또는 단순 더미 벡터 (API 없을 때)."""
    global _embed_fn
    if _embed_fn is not None:
        return _embed_fn(text)

    if not EMBEDDING_API_KEY:
        logger.warning("EMBEDDING_API_KEY not set; using zero vector for RAG")
        return [0.0] * min(EMBEDDING_DIMENSION, 384)

    try:
        import httpx
        url = "https://api.upstage.ai/v1/solar/embeddings"
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                url,
                headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
                json={"model": EMBEDDING_MODEL, "input": text[:8000]},
            )
            r.raise_for_status()
            data = r.json()
            emb = data.get("data", [{}])[0].get("embedding", [])
            if emb:
                return emb[:EMBEDDING_DIMENSION]
    except Exception as e:
        logger.warning("Embedding API failed: %s", e)

    return [0.0] * min(EMBEDDING_DIMENSION, 384)


def _get_collection():
    """ChromaDB Persistent Client + complaint_cases 컬렉션."""
    global _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        _collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except Exception as e:
        logger.warning("ChromaDB not available: %s", e)
        return None


async def search_similar_complaints(query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
    """유사 민원 검색. 실패 시 빈 리스트."""
    coll = _get_collection()
    if coll is None:
        return []

    try:
        emb = _get_embedding(query_text)
        res = coll.query(
            query_embeddings=[emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        out = []
        docs = (res.get("documents") or [[]])[0]
        metadatas = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]
        for i, doc in enumerate(docs):
            meta = (metadatas or [{}])[i] if metadatas else {}
            out.append({
                "document": doc or "",
                "summary": doc[:500] if doc else "",
                "response_snippet": meta.get("response_snippet", ""),
                "complaint_type": meta.get("complaint_type", ""),
                "complaint_id": meta.get("complaint_id"),
            })
        return out
    except Exception as e:
        logger.warning("ChromaDB query failed: %s", e)
        return []


def index_complaint(
    complaint_id: int,
    summary_text: str,
    complaint_type: str,
    response_snippet: str,
    urgency: str = "",
) -> None:
    """민원 1건을 ChromaDB에 인덱싱 (처리 완료 후 호출)."""
    coll = _get_collection()
    if coll is None:
        return
    doc_id = f"complaint_{complaint_id}"
    document = f"{summary_text}\n유형: {complaint_type}\n응답 요약: {response_snippet[:500]}"
    try:
        emb = _get_embedding(document)
        coll.upsert(
            ids=[doc_id],
            embeddings=[emb],
            documents=[document],
            metadatas=[{
                "complaint_id": complaint_id,
                "complaint_type": complaint_type,
                "urgency": urgency,
                "response_snippet": response_snippet[:500],
            }],
        )
        logger.info("Indexed complaint %s for RAG", complaint_id)
    except Exception as e:
        logger.warning("RAG index failed for %s: %s", complaint_id, e)
