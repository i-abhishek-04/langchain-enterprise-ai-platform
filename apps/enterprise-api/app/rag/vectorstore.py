import logging
import math
import re
import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.config import settings

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except ImportError:
    QdrantClient = None
    qmodels = None

logger = logging.getLogger(__name__)
EMBEDDING_DIMENSION = 384
_in_memory_docs: List[Dict[str, Any]] = []
COMMON_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "about",
    "and", "or", "not", "no", "what", "which", "who", "whom", "this",
    "that", "these", "those", "how", "why", "where", "when", "key",
    "available", "does", "do", "it", "this", "their", "they", "i",
}


@lru_cache(maxsize=1)
def _embedding_model():
    from fastembed import TextEmbedding

    return TextEmbedding(
        model_name=settings.EMBEDDING_MODEL,
        cache_dir=settings.EMBEDDING_CACHE_DIR,
    )


def embed_texts(texts: Sequence[str]) -> List[List[float]]:
    """Encode text with the configured CPU-friendly, 384-dimensional model."""
    if not texts:
        return []
    vectors = _embedding_model().embed(list(texts))
    return [vector.tolist() for vector in vectors]


def _doc_from_payload(payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not payload or not payload.get("text"):
        return None
    return {
        "text": payload["text"],
        "filename": payload.get("filename", "unknown"),
        "page": payload.get("page", 1),
        "chunk_id": payload.get("chunk_id", 0),
    }


def _remember_docs(docs: Sequence[Dict[str, Any]]) -> None:
    known = {
        (doc["filename"], doc.get("chunk_id", 0), doc["text"])
        for doc in _in_memory_docs
    }
    for doc in docs:
        key = (doc["filename"], doc.get("chunk_id", 0), doc["text"])
        if key not in known:
            _in_memory_docs.append(dict(doc))
            known.add(key)


def get_qdrant_client():
    if QdrantClient is None:
        return None
    try:
        client = QdrantClient(url=settings.QDRANT_URL, timeout=2.0)
        client.get_collections()
        return client
    except Exception as exc:
        logger.warning("Qdrant unavailable; using in-memory lexical retrieval: %s", exc)
        return None


def _scroll_collection(client, collection_name: str):
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=collection_name,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        yield from records
        if offset is None:
            break


def _migrate_legacy_collection(client) -> None:
    legacy_name = settings.LEGACY_QDRANT_COLLECTION
    if legacy_name == settings.QDRANT_COLLECTION:
        return
    existing = {
        collection.name for collection in client.get_collections().collections
    }
    if legacy_name not in existing:
        return

    legacy_records = [
        (record, doc)
        for record in _scroll_collection(client, legacy_name)
        if (doc := _doc_from_payload(record.payload)) is not None
    ]
    if not legacy_records:
        return

    logger.info(
        "Re-embedding %d chunks from legacy Qdrant collection '%s'.",
        len(legacy_records),
        legacy_name,
    )
    docs = [doc for _, doc in legacy_records]
    vectors = embed_texts([doc["text"] for doc in docs])
    points = [
        qmodels.PointStruct(
            id=record.id,
            vector=vector,
            payload=doc,
        )
        for (record, doc), vector in zip(legacy_records, vectors)
    ]
    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)


def init_qdrant_collection() -> None:
    client = get_qdrant_client()
    if client is None or qmodels is None:
        return

    collections = {
        collection.name for collection in client.get_collections().collections
    }
    if settings.QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=qmodels.VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=qmodels.Distance.COSINE,
            ),
        )

    _migrate_legacy_collection(client)
    docs = [
        doc
        for record in _scroll_collection(client, settings.QDRANT_COLLECTION)
        if (doc := _doc_from_payload(record.payload)) is not None
    ]
    _remember_docs(docs)


def upsert_chunks(chunks: List[Dict[str, Any]]) -> int:
    if not chunks:
        return 0

    docs = [
        {
            "text": chunk["text"],
            "filename": chunk["filename"],
            "page": chunk.get("page", 1),
            "chunk_id": chunk.get("chunk_id", 0),
        }
        for chunk in chunks
    ]
    client = get_qdrant_client()
    if client is not None and qmodels is not None:
        vectors = embed_texts([doc["text"] for doc in docs])
        points = [
            qmodels.PointStruct(
                id=uuid.uuid4().hex,
                vector=vector,
                payload=doc,
            )
            for doc, vector in zip(docs, vectors)
        ]
        client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)

    _remember_docs(docs)
    return len(docs)


def _terms(text: str) -> List[str]:
    terms = [
        token.lower()
        for token in re.findall(r"\w+", text)
        if len(token) > 2 and token.lower() not in COMMON_STOP_WORDS
    ]
    return terms or [
        token.lower()
        for token in re.findall(r"\w+", text)
        if len(token) > 2
    ]


def _keyword_scores(query: str, docs: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    query_terms = set(_terms(query))
    if not query_terms or not docs:
        return {}

    tokenized_docs = [_terms(doc["text"]) for doc in docs]
    average_length = sum(map(len, tokenized_docs)) / max(len(tokenized_docs), 1)
    document_frequency = {
        term: sum(term in set(tokens) for tokens in tokenized_docs)
        for term in query_terms
    }
    raw_scores: List[float] = []
    for tokens in tokenized_docs:
        frequencies = {term: tokens.count(term) for term in query_terms}
        score = 0.0
        for term, frequency in frequencies.items():
            if frequency == 0:
                continue
            inverse_frequency = (
                math.log(
                    1
                    + (len(docs) - document_frequency[term] + 0.5)
                    / (document_frequency[term] + 0.5)
                )
            )
            length_norm = frequency + 1.5 * (
                1 - 0.75 + 0.75 * len(tokens) / max(average_length, 1)
            )
            score += inverse_frequency * frequency * 2.5 / length_norm
        raw_scores.append(score)

    max_score = max(raw_scores, default=0.0)
    return {
        doc["text"]: score / max_score
        for doc, score in zip(docs, raw_scores)
        if score > 0 and max_score > 0
    }


def search_similar_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Combine semantic similarity and BM25-style keyword relevance."""
    if top_k <= 0:
        return []

    client = get_qdrant_client()
    vector_hits: Dict[str, Tuple[Dict[str, Any], float]] = {}
    if client is not None:
        query_vector = embed_texts([query])[0]
        response = client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            limit=max(top_k * 4, top_k),
            with_payload=True,
        )
        for point in response.points:
            doc = _doc_from_payload(point.payload)
            if doc is not None:
                vector_hits[doc["text"]] = (
                    doc,
                    max(0.0, min(1.0, float(point.score))),
                )

    candidate_docs = list({doc["text"]: doc for doc in _in_memory_docs}.values())
    candidate_texts = {doc["text"] for doc in candidate_docs}
    for doc, _ in vector_hits.values():
        if doc["text"] not in candidate_texts:
            candidate_docs.append(doc)
            candidate_texts.add(doc["text"])

    keyword_scores = _keyword_scores(query, candidate_docs)
    fused: List[Tuple[float, Dict[str, Any]]] = []
    for doc in candidate_docs:
        vector_score = vector_hits.get(doc["text"], ({}, 0.0))[1]
        keyword_score = keyword_scores.get(doc["text"], 0.0)
        if vector_score == 0 and keyword_score == 0:
            continue
        score = 0.6 * vector_score + 0.4 * keyword_score
        fused.append((score, doc))

    fused.sort(key=lambda result: result[0], reverse=True)
    return [
        {
            "text": doc["text"],
            "filename": doc["filename"],
            "page": doc.get("page", 1),
            "score": round(score, 4),
        }
        for score, doc in fused[:top_k]
    ]
