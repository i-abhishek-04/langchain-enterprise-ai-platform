import os
import shutil
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core import security
from app.rag.ingestion import process_and_index_document
from app.rag.vectorstore import _in_memory_docs
from app.agents.workflow import execute_multi_agent_pipeline

router = APIRouter()

# --- Auth Pydantic Schemas ---
class UserAuthSchema(BaseModel):
    email: str
    password: str

class ChatRequestSchema(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"
    provider_id: Optional[str] = "groq"
    model_id: Optional[str] = "llama-3.3-70b-versatile"
    api_key: Optional[str] = ""

# --- Authentication Endpoints ---
@router.post("/auth/register")
def register_user(payload: UserAuthSchema, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
        
    hashed = security.get_password_hash(payload.password)
    user = models.User(email=payload.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = security.create_access_token({"sub": user.email, "id": user.id})
    return {"access_token": token, "token_type": "bearer", "user": {"email": user.email, "id": user.id}}

@router.post("/auth/login")
def login_user(payload: UserAuthSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    token = security.create_access_token({"sub": user.email, "id": user.id})
    return {"access_token": token, "token_type": "bearer", "user": {"email": user.email, "id": user.id}}

# --- Document Ingestion & RAG Endpoints ---
@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    allowed_exts = [".pdf", ".docx", ".txt", ".md", ".markdown"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types: {', '.join(allowed_exts)}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = process_and_index_document(tmp_path, file.filename)
        doc_rec = models.DocumentRecord(
            filename=file.filename,
            file_type=ext,
            chunk_count=result["chunk_count"],
            status="INDEXED"
        )
        db.add(doc_rec)
        db.commit()
        db.refresh(doc_rec)
        return {"message": "Document indexed successfully in Qdrant.", "document": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
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
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.DocumentRecord).filter(models.DocumentRecord.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.filename}' deleted successfully."}

# --- Multi-Agent Chat Endpoint ---
@router.post("/chat")
def chat_with_multi_agent(payload: ChatRequestSchema, db: Session = Depends(get_db)):
    agent_result = execute_multi_agent_pipeline(
        query=payload.query,
        session_id=payload.session_id,
        provider_id=payload.provider_id,
        model_id=payload.model_id,
        api_key=payload.api_key
    )

    # Persist Chat History
    chat_rec = models.ChatHistory(
        session_id=payload.session_id,
        user_query=payload.query,
        bot_response=agent_result["final_response"],
        provider_id=payload.provider_id,
        model_id=payload.model_id
    )
    db.add(chat_rec)

    # Persist Observability Log
    eval_log = models.EvaluationLog(
        session_id=payload.session_id,
        user_query=payload.query,
        retrieved_context=agent_result.get("context_text", ""),
        bot_response=agent_result["final_response"],
        latency_ms=agent_result["latency_ms"],
        prompt_tokens=len(payload.query.split()),
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
def get_chat_history(session_id: Optional[str] = "default_session", db: Session = Depends(get_db)):
    history = db.query(models.ChatHistory)\
        .filter(models.ChatHistory.session_id == session_id)\
        .order_by(models.ChatHistory.created_at.asc()).all()
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
def get_evaluation_metrics(db: Session = Depends(get_db)):
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
def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    total_docs = db.query(models.DocumentRecord).count()
    total_queries = db.query(models.EvaluationLog).count()
    hallucination_count = db.query(models.EvaluationLog).filter(models.EvaluationLog.is_hallucinated == True).count()
    guardrail_count = db.query(models.EvaluationLog).filter(models.EvaluationLog.guardrail_flagged == True).count()
    
    logs = db.query(models.EvaluationLog).all()
    avg_latency = round(sum(l.latency_ms for l in logs) / (len(logs) or 1), 2)
    
    return {
        "active_documents": total_docs,
        "total_queries_processed": total_queries,
        "avg_latency_ms": avg_latency,
        "hallucination_count": hallucination_count,
        "guardrail_flags_count": guardrail_count,
        "active_users": 1,
        "most_used_model": "Llama 3.3 70B (Groq Free)"
    }
