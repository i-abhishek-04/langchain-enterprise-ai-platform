import os
import tempfile
import atexit
import pytest

# Set SECRET_KEY and temporary DATABASE_URL before any app modules are loaded
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-automated-testing-only-12345")

_temp_db_path = None
if "DATABASE_URL" not in os.environ:
    _temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    _temp_db_file.close()
    _temp_db_path = _temp_db_file.name
    os.environ["DATABASE_URL"] = f"sqlite:///{_temp_db_path.replace(os.sep, '/')}"

def _cleanup_temp_db():
    global _temp_db_path
    if _temp_db_path and os.path.exists(_temp_db_path):
        try:
            from app.db.database import engine
            engine.dispose()
        except Exception:
            pass
        try:
            os.remove(_temp_db_path)
            _temp_db_path = None
        except Exception:
            pass

atexit.register(_cleanup_temp_db)

def pytest_sessionfinish(session, exitstatus):
    _cleanup_temp_db()

@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db_fixture():
    yield
    _cleanup_temp_db()
