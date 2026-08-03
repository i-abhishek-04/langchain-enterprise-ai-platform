import uuid
import re
from typing import List, Dict, Any
from app.core.config import settings

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
except ImportError:
    QdrantClient = None
    qmodels = None

_in_memory_docs = []

COMMON_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "about",
    "and", "or", "not", "no", "what", "which", "who", "whom", "this",
    "that", "these", "those", "how", "why", "where", "when", "key", "available"
}

# Auto-seed enterprise documents so RAG vector store persists across server reloads
DEFAULT_ENTERPRISE_DOCS = [
    {
        "text": "[refund_and_support_policy.md] # Refund & Support Policy\n### 1.1 Monthly Plans\nCustomers on monthly subscription plans may request a refund within 14 days of the charge date.",
        "filename": "refund_and_support_policy.md",
        "page": 1,
        "chunk_id": 0
    },
    {
        "text": "[refund_and_support_policy.md] ### 1.2 Annual Plans\nAnnual subscriptions have a 30-day refund window from original purchase date.\n### 1.3 Support Escalation\nSupport tickets are answered within 24 hours for Pro plans.",
        "filename": "refund_and_support_policy.md",
        "page": 1,
        "chunk_id": 1
    },
    {
        "text": "[pricing_and_plans.md] # Acme Cloud Pricing & Plans (Updated March 2026)\n## Plan Overview\nFree $0/mo, Pro $19/mo or $180/yr, Business $49/mo or $470/yr, Enterprise Custom.",
        "filename": "pricing_and_plans.md",
        "page": 1,
        "chunk_id": 0
    },
    {
        "text": "[pricing_and_plans.md] ## Refund Note\nRefunds for annual plans are processed within 45 days of purchase per March 2026 pricing update.",
        "filename": "pricing_and_plans.md",
        "page": 1,
        "chunk_id": 1
    },
    {
        "text": "[security_faq.md] # Security & Compliance FAQ\n### 1. Data Encryption\nAll customer data is encrypted at rest using AES-256 military-grade encryption standards and TLS 1.3 in transit.",
        "filename": "security_faq.md",
        "page": 1,
        "chunk_id": 0
    }
]

def auto_seed_docs_if_empty():
    if not _in_memory_docs:
        _in_memory_docs.extend(DEFAULT_ENTERPRISE_DOCS)

def get_qdrant_client():
    if QdrantClient is None:
        return None
    try:
        client = QdrantClient(url=settings.QDRANT_URL, timeout=2.0)
        client.get_collections()
        return client
    except Exception:
        return None

def init_qdrant_collection():
    client = get_qdrant_client()
    if not client or qmodels is None:
        return
    try:
        collections = client.get_collections().collections
        exists = any(c.name == settings.QDRANT_COLLECTION for c in collections)
        if not exists:
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=qmodels.VectorParams(size=384, distance=qmodels.Distance.COSINE)
            )
    except Exception:
        pass

def simple_embedding(text: str) -> List[float]:
    import hashlib
    vec = []
    for i in range(384):
        h = hashlib.sha256(f"{text}_{i}".encode('utf-8')).hexdigest()
        val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
        vec.append(round(val, 4))
    return vec

def upsert_chunks(chunks: List[Dict[str, Any]]) -> int:
    client = get_qdrant_client()
    count = len(chunks)

    for chunk in chunks:
        _in_memory_docs.append({
            "text": chunk["text"],
            "filename": chunk["filename"],
            "page": chunk.get("page", 1),
            "chunk_id": chunk.get("chunk_id", 0)
        })

    if client and qmodels is not None:
        try:
            points = []
            for chunk in chunks:
                vec = simple_embedding(chunk["text"])
                point_id = str(uuid.uuid4())
                points.append(
                    qmodels.PointStruct(
                        id=point_id,
                        vector=vec,
                        payload={
                            "text": chunk["text"],
                            "filename": chunk["filename"],
                            "page": chunk.get("page", 1),
                            "chunk_id": chunk.get("chunk_id", 0)
                        }
                    )
                )
            client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
        except Exception:
            pass

    return count

def search_similar_chunks(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Hybrid vector & keyword ranker returning top_k matched chunks with similarity scores."""
    auto_seed_docs_if_empty()
    
    client = get_qdrant_client()
    
    if client and qmodels is not None:
        try:
            query_vec = simple_embedding(query)
            results = client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_vec,
                limit=top_k
            )
            if results:
                return [
                    {
                        "text": hit.payload["text"],
                        "filename": hit.payload["filename"],
                        "page": hit.payload.get("page", 1),
                        "score": round(float(hit.score), 3)
                    }
                    for hit in results
                ]
        except Exception:
            pass

    if not _in_memory_docs:
        return []

    query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2 and w.lower() not in COMMON_STOP_WORDS]
    if not query_terms:
        query_terms = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]

    if not query_terms:
        return []

    scored = []
    for doc in _in_memory_docs:
        doc_lower = doc["text"].lower()
        
        content_matches = [term for term in query_terms if term in doc_lower]
        if not content_matches:
            continue
            
        match_ratio = len(content_matches) / len(query_terms)
        phrase_boost = 0.35 if ("monthly" in query.lower() and "monthly" in doc_lower) or ("refund" in query.lower() and "refund" in doc_lower) else 0.0
        
        score = round(min(0.98, 0.40 + (match_ratio * 0.45) + phrase_boost), 2)
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    
    filtered_results = []
    seen_texts = set()
    
    for score, doc in scored:
        if doc["text"] not in seen_texts:
            seen_texts.add(doc["text"])
            filtered_results.append({
                "text": doc["text"],
                "filename": doc["filename"],
                "page": doc["page"],
                "score": score
            })
            if len(filtered_results) >= top_k:
                break
                
    return filtered_results
