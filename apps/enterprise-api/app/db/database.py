from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


def make_database_url(database_url: str) -> URL:
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        return url.set(drivername="postgresql+psycopg")
    return url


# Handle SQLite vs PostgreSQL engine options
database_url = make_database_url(settings.DATABASE_URL)
connect_args = (
    {"check_same_thread": False}
    if database_url.get_backend_name() == "sqlite"
    else {}
)

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
