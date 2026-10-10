from uuid import uuid4

from app.core.security import create_access_token
from app.db.database import SessionLocal
from app.db.models import User


def create_test_auth(is_admin=False):
    email = f"test-{uuid4().hex}@example.com"
    db = SessionLocal()
    try:
        user = User(email=email, hashed_password="unused-test-hash", is_admin=is_admin)
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": user.email, "id": user.id})
        return {"Authorization": f"Bearer {token}"}, user.id, user.email
    finally:
        db.close()
