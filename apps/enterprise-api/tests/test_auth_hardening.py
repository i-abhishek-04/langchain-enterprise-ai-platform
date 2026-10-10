import inspect
import os
import sys
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import desc, func

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api import router
from app.db.database import SessionLocal
from app.db.models import ChatHistory, EvaluationLog, User
from app.main import app
from auth_helpers import create_test_auth


client = TestClient(app)


def test_auth_required_and_admin_routes_are_role_protected():
    user_headers, _, _ = create_test_auth()

    assert client.get("/api/v1/documents").status_code == 401
    assert client.get("/api/v1/documents", headers=user_headers).status_code == 200
    assert client.get("/api/v1/admin/stats", headers=user_headers).status_code == 403


def test_auth_schemas_validate_email_and_password():
    invalid_email = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "long-enough"},
    )
    short_password = client.post(
        "/api/v1/auth/register",
        json={"email": f"{uuid4().hex}@example.com", "password": "short"},
    )
    assert invalid_email.status_code == 422
    assert short_password.status_code == 422


def test_admin_email_is_promoted_at_registration():
    email = f"{uuid4().hex}@example.com"
    with patch.object(router.settings, "ADMIN_EMAIL", email):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "correct horse battery"},
        )

    assert response.status_code == 200
    assert response.json()["user"]["is_admin"] is True


def test_login_rate_limit_returns_retry_after():
    router._auth_attempts.clear()
    with patch.object(router, "AUTH_RATE_LIMIT", 1):
        first = client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "incorrect-password"},
        )
        second = client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "incorrect-password"},
        )

    assert first.status_code == 401
    assert second.status_code == 429
    assert int(second.headers["Retry-After"]) > 0


def test_register_rate_limit_returns_retry_after():
    router._auth_attempts.clear()
    with patch.object(router, "AUTH_RATE_LIMIT", 1):
        first = client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid4().hex}@example.com", "password": "long-enough-password"},
        )
        second = client.post(
            "/api/v1/auth/register",
            json={"email": f"{uuid4().hex}@example.com", "password": "long-enough-password"},
        )

    assert first.status_code == 200
    assert second.status_code == 429
    assert int(second.headers["Retry-After"]) > 0


def test_admin_statistics_use_database_values():
    headers, _, _ = create_test_auth(is_admin=True)
    model_id = f"test-model-{uuid4().hex}"
    db = SessionLocal()
    try:
        db.add(
            EvaluationLog(
                user_query="test query",
                bot_response="test response",
                model_id=model_id,
                latency_ms=42,
            )
        )
        db.commit()
        expected_active_users = db.query(User).filter(User.is_active.is_(True)).count()
        expected_model = (
            db.query(EvaluationLog.model_id)
            .group_by(EvaluationLog.model_id)
            .order_by(desc(func.count(EvaluationLog.id)))
            .first()[0]
        )
    finally:
        db.close()

    response = client.get("/api/v1/admin/stats", headers=headers)
    assert response.status_code == 200
    assert response.json()["active_users"] == expected_active_users
    assert response.json()["most_used_model"] == expected_model


def test_history_is_scoped_to_authenticated_user_even_for_same_session():
    first_headers, first_user_id, _ = create_test_auth()
    _, second_user_id, _ = create_test_auth()
    session_id = f"shared-{uuid4().hex}"
    db = SessionLocal()
    try:
        db.add_all(
            [
                ChatHistory(
                    session_id=session_id,
                    user_id=first_user_id,
                    user_query="first user's private question",
                    bot_response="private response",
                ),
                ChatHistory(
                    session_id=session_id,
                    user_id=second_user_id,
                    user_query="second user's private question",
                    bot_response="other response",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/api/v1/history",
        params={"session_id": session_id},
        headers=first_headers,
    )

    assert response.status_code == 200
    assert [item["user_query"] for item in response.json()["history"]] == [
        "first user's private question"
    ]


def test_upload_handler_is_sync_and_does_not_expose_internal_errors():
    headers, _, _ = create_test_auth()
    assert not inspect.iscoroutinefunction(router.upload_document)

    with patch.object(
        router,
        "process_and_index_document",
        side_effect=RuntimeError("private filesystem path"),
    ):
        response = client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files={"file": ("document.txt", b"contents", "text/plain")},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Document ingestion failed. Please try again later."
    assert "private filesystem path" not in response.text
