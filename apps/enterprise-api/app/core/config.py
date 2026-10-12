import os
import secrets

try:
    from pydantic_settings import BaseSettings
    from pydantic import model_validator
except ImportError:
    BaseSettings = object
    model_validator = None

class Settings(BaseSettings if BaseSettings is not object else object):
    PROJECT_NAME: str = "AI Document Q&A API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # JWT Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "").strip().lower()

    # Database (PostgreSQL or SQLite fallback)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise_ai.db")

    # Vector Database (Qdrant container or in-memory)
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "enterprise_documents_v2")
    LEGACY_QDRANT_COLLECTION: str = os.getenv(
        "LEGACY_QDRANT_COLLECTION", "enterprise_documents"
    )
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_CACHE_DIR: str = os.getenv(
        "EMBEDDING_CACHE_DIR",
        os.path.join(os.path.expanduser("~"), ".cache", "fastembed"),
    )

    # Free Tier AI Keys
    ALLOW_SERVER_KEY: bool = os.getenv("ALLOW_SERVER_KEY", "false").strip().lower() in {"true", "1", "yes"}
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    if model_validator is not None:
        @model_validator(mode="after")
        def _validate_secret_key(self):
            key = (getattr(self, "SECRET_KEY", None) or os.getenv("SECRET_KEY", "")).strip()
            if not key:
                raise RuntimeError(
                    "SECRET_KEY environment variable is required and must not be empty."
                )
            self.SECRET_KEY = key
            return self
    else:
        def __init__(self, **values):
            super().__init__(**values)
            key = (getattr(self, "SECRET_KEY", None) or os.getenv("SECRET_KEY", "")).strip()
            if not key:
                raise RuntimeError(
                    "SECRET_KEY environment variable is required and must not be empty."
                )
            self.SECRET_KEY = key

settings = Settings()
