import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="INDEXED") # INDEXED, PROCESSING, FAILED

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_query = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    provider_id = Column(String, default="groq")
    model_id = Column(String, default="llama-3.3-70b-versatile")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_query = Column(Text, nullable=False)
    retrieved_context = Column(Text, nullable=True)
    bot_response = Column(Text, nullable=False)
    latency_ms = Column(Float, default=0.0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    confidence_score = Column(Float, default=1.0)
    citation_count = Column(Integer, default=0)
    guardrail_flagged = Column(Boolean, default=False)
    guardrail_reason = Column(String, nullable=True)
    is_hallucinated = Column(Boolean, default=False)
    provider_id = Column(String, default="groq")
    model_id = Column(String, default="llama-3.3-70b-versatile")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
