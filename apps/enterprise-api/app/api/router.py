import os
import shutil
import tempfile
import logging
import threading
import time
from math import ceil
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.database import get_db
from app.db import models
from app.core import security
from app.core.config import settings
from app.rag.ingestion import process_and_index_document
from app.rag.vectorstore import delete_document_chunks
from app.agents.workflow import execute_multi_agent_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)
AUTH_RATE_LIMIT = 10
AUTH_RATE_WINDOW_SECONDS = 60
_auth_attempts: dict[tuple[str, str], tuple[float, int]] = {}
_auth_attempts_lock = threading.Lock()

CHAT_RATE_LIMIT = 30
CHAT_RATE_WINDOW_SECONDS = 60
_chat_attempts: dict[int, tuple[float, int]] = {}
_chat_attempts_lock = threading.Lock()
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

# --- Auth Pydantic Schemas ---
class UserAuthSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_bcrypt_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes when encoded as UTF-8.")
        return value

class ChatRequestSchema(BaseModel):
    query: str = Field(..., max_length=8000)
    session_id: Optional[str] = "default_session"
    provider_id: Optional[str] = "groq"
    model_id: Optional[str] = "llama-3.3-70b-versatile"
    api_key: Optional[str] = ""


def resolve_api_key(payload_key: Optional[str] = None, settings: Any = None) -> str:
    """
    Resolve API key:
    - Use payload_key if non-empty
    - Otherwise, use settings.GROQ_API_KEY only if settings.ALLOW_SERVER_KEY is True
    - Defaults to empty string (server key disabled by default)
    """
    if payload_key and payload_key.strip():
        return payload_key.strip()
    from app.core.config import settings as global_settings
    active_settings = settings if settings is not None else global_settings
    if getattr(active_settings, "ALLOW_SERVER_KEY", False):
        return (getattr(active_settings, "GROQ_API_KEY", "") or "").strip()
    return ""


def _enforce_auth_rate_limit(request: Request, action: str) -> None:
    client_host = request.client.host if request.client else "unknown"
    key = (action, client_host)
    now = time.monotonic()
    with _auth_attempts_lock:
        expired = [
            attempt_key
            for attempt_key, (started_at, _) in _auth_attempts.items()
            if now - started_at >= AUTH_RATE_WINDOW_SECONDS
        ]
        for attempt_key in expired:
            del _auth_attempts[attempt_key]

        started_at, count = _auth_attempts.get(key, (now, 0))
        if now - started_at >= AUTH_RATE_WINDOW_SECONDS:
            started_at, count = now, 0
        if count >= AUTH_RATE_LIMIT:
            retry_after = max(1, ceil(AUTH_RATE_WINDOW_SECONDS - (now - started_at)))
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )
        _auth_attempts[key] = (started_at, count + 1)


def _enforce_chat_rate_limit(user_id: int) -> None:
    now = time.monotonic()
    with _chat_attempts_lock:
        expired = [
            uid
            for uid, (started_at, _) in _chat_attempts.items()
            if now - started_at >= CHAT_RATE_WINDOW_SECONDS
        ]
        for uid in expired:
            del _chat_attempts[uid]

        started_at, count = _chat_attempts.get(user_id, (now, 0))
        if now - started_at >= CHAT_RATE_WINDOW_SECONDS:
            started_at, count = now, 0
        if count >= CHAT_RATE_LIMIT:
            retry_after = max(1, ceil(CHAT_RATE_WINDOW_SECONDS - (now - started_at)))
            raise HTTPException(
                status_code=429,
                detail="Chat rate limit exceeded. Please wait before sending another message.",
                headers={"Retry-After": str(retry_after)},
            )
        _chat_attempts[user_id] = (started_at, count + 1)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    unauthorized = HTTPException(
        status_code=401,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    payload = security.decode_access_token(credentials.credentials)
    if not payload:
        raise unauthorized
    user_id = payload.get("id")
    email = payload.get("sub")
    if not isinstance(user_id, int) or not isinstance(email, str):
        raise unauthorized

    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.email == email,
    ).first()
    if user is None or not user.is_active:
        raise unauthorized
    return user


def get_current_admin_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return current_user


def _auth_response(user: models.User) -> dict:
    token = security.create_access_token({"sub": user.email, "id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "id": user.id,
            "is_admin": user.is_admin,
        },
    }


# --- Authentication Endpoints ---
@router.post("/auth/register")
def register_user(
    payload: UserAuthSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    _enforce_auth_rate_limit(request, "register")
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
        
    hashed = security.get_password_hash(payload.password)
    user = models.User(
        email=payload.email,
        hashed_password=hashed,
        is_admin=bool(settings.ADMIN_EMAIL and payload.email == settings.ADMIN_EMAIL),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_response(user)

@router.post("/auth/login")
def login_user(
    payload: UserAuthSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    _enforce_auth_rate_limit(request, "login")
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if (
        not user
        or not user.is_active
        or not security.verify_password(payload.password, user.hashed_password)
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return _auth_response(user)

# --- Document Ingestion & RAG Endpoints ---
@router.post("/documents/upload")
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    allowed_exts = [".pdf", ".docx", ".txt", ".md", ".markdown"]
    filename = os.path.basename(file.filename or "upload")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types: {', '.join(allowed_exts)}")

    file_bytes = file.file.read(MAX_UPLOAD_SIZE + 1)
    if len(file_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds the maximum allowed limit of 10 MB.",
        )
    file.file.seek(0)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)
        result = process_and_index_document(tmp_path, filename)
        doc_rec = models.DocumentRecord(
            filename=filename,
            file_type=ext,
            chunk_count=result["chunk_count"],
            status="INDEXED"
        )
        db.add(doc_rec)
        db.commit()
        db.refresh(doc_rec)
        return {"message": "Document indexed successfully in Qdrant.", "document": result}
    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        logger.exception("Document ingestion failed for %s", filename)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed. Please try again later.",
        ) from None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    docs = db.query(models.DocumentRecord).order_by(models.DocumentRecord.uploaded_at.desc()).all()
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "chunk_count": d.chunk_count,
                "status": d.status,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else ""
            }
            for d in docs
        ]
    }

@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.DocumentRecord).filter(models.DocumentRecord.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    filename = doc.filename
    db.delete(doc)
    db.commit()
    delete_document_chunks(filename=filename)
    return {"message": f"Document '{filename}' deleted successfully."}

# --- Multi-Agent Chat Endpoint ---
@router.post("/chat")
def chat_with_multi_agent(
    payload: ChatRequestSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _enforce_chat_rate_limit(current_user.id)
    effective_api_key = resolve_api_key(payload.api_key, settings)

    agent_result = execute_multi_agent_pipeline(
        query=payload.query,
        session_id=payload.session_id,
        provider_id=payload.provider_id,
        model_id=payload.model_id,
        api_key=effective_api_key
    )

    sanitized_query = agent_result.get("sanitized_query", payload.query)

    # Persist Chat History
    chat_rec = models.ChatHistory(
        session_id=payload.session_id,
        user_id=current_user.id,
        user_query=sanitized_query,
        bot_response=agent_result["final_response"],
        provider_id=payload.provider_id,
        model_id=payload.model_id
    )
    db.add(chat_rec)

    # Persist Observability Log
    eval_log = models.EvaluationLog(
        session_id=payload.session_id,
        user_query=sanitized_query,
        retrieved_context=agent_result.get("context_text", ""),
        bot_response=agent_result["final_response"],
        latency_ms=agent_result["latency_ms"],
        prompt_tokens=len(sanitized_query.split()),
        completion_tokens=len(agent_result["final_response"].split()),
        confidence_score=agent_result["confidence_score"],
        citation_count=agent_result["citation_count"],
        guardrail_flagged=agent_result["guardrail_flagged"],
        guardrail_reason=agent_result["guardrail_reason"],
        is_hallucinated=agent_result["is_hallucinated"],
        provider_id=payload.provider_id,
        model_id=payload.model_id
    )
    db.add(eval_log)
    db.commit()

    return {
        "response": agent_result["final_response"],
        "confidence_score": agent_result["confidence_score"],
        "citations": agent_result["retrieved_chunks"],
        "agent_logs": agent_result["agent_logs"],
        "is_fallback_mode": agent_result.get("is_fallback_mode", False),
        "fallback_reason": agent_result.get("fallback_reason", ""),
        "metrics": {
            "latency_ms": agent_result["latency_ms"],
            "total_tokens": agent_result["total_tokens"],
            "confidence": agent_result["confidence_score"],
            "citation_count": agent_result["citation_count"],
            "guardrail_flagged": agent_result["guardrail_flagged"]
        }
    }

# --- Observability, History & Admin Endpoints ---
@router.get("/history")
def get_chat_history(
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == current_user.id
    )
    if session_id:
        query = query.filter(models.ChatHistory.session_id == session_id)
    history = query.order_by(models.ChatHistory.created_at.asc()).all()
    return {
        "history": [
            {
                "id": h.id,
                "user_query": h.user_query,
                "bot_response": h.bot_response,
                "created_at": h.created_at.isoformat() if h.created_at else ""
            }
            for h in history
        ]
    }

@router.get("/metrics")
def get_evaluation_metrics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    logs = db.query(models.EvaluationLog).order_by(models.EvaluationLog.created_at.desc()).limit(50).all()
    avg_latency = round(sum(l.latency_ms for l in logs) / (len(logs) or 1), 2)
    avg_confidence = round(sum(l.confidence_score for l in logs) / (len(logs) or 1), 2)
    total_tokens = sum(l.prompt_tokens + l.completion_tokens for l in logs)

    return {
        "summary": {
            "total_queries": len(logs),
            "avg_latency_ms": avg_latency,
            "avg_confidence_score": avg_confidence,
            "total_tokens_consumed": total_tokens,
            "estimated_cost_saved": f"${round(total_tokens * 0.00002, 4)} (Free Tier)"
        },
        "logs": [
            {
                "id": l.id,
                "user_query": l.user_query,
                "latency_ms": l.latency_ms,
                "confidence_score": l.confidence_score,
                "citation_count": l.citation_count,
                "guardrail_flagged": l.guardrail_flagged,
                "is_hallucinated": l.is_hallucinated,
                "created_at": l.created_at.isoformat() if l.created_at else ""
            }
            for l in logs
        ]
    }

@router.get("/admin/stats")
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    total_docs = db.query(models.DocumentRecord).count()
    total_queries = db.query(models.EvaluationLog).count()
    hallucination_count = db.query(models.EvaluationLog).filter(models.EvaluationLog.is_hallucinated == True).count()
    guardrail_count = db.query(models.EvaluationLog).filter(models.EvaluationLog.guardrail_flagged == True).count()
    
    avg_latency = round(
        db.query(func.avg(models.EvaluationLog.latency_ms)).scalar() or 0.0,
        2,
    )
    active_users = db.query(models.User).filter(models.User.is_active.is_(True)).count()
    most_used_model_row = (
        db.query(models.EvaluationLog.model_id)
        .filter(models.EvaluationLog.model_id.isnot(None))
        .group_by(models.EvaluationLog.model_id)
        .order_by(desc(func.count(models.EvaluationLog.id)))
        .first()
    )
    
    return {
        "active_documents": total_docs,
        "total_queries_processed": total_queries,
        "avg_latency_ms": avg_latency,
        "hallucination_count": hallucination_count,
        "guardrail_flags_count": guardrail_count,
        "active_users": active_users,
        "most_used_model": most_used_model_row[0] if most_used_model_row else None,
    }
