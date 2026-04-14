from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, deps, models
from app.database import Base
from app.main import app
import app.main as app_main
from app.utils import security


def _create_ticket(db_session, user_id: int, ticket_uid: str):
    ticket = models.Ticket(
        ticket_uid=ticket_uid,
        user_id=user_id,
        image_url=f"https://img/{ticket_uid}.jpg",
        poem_content=f"poem-{ticket_uid}",
        user_diary_summary=f"diary-{ticket_uid}",
        island_category="RAIN",
        selected_tags=["#测试"],
        is_public=False,
        is_printed_intent=False,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def test_users_me_returns_live_ticket_count():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session = testing_session_local()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[deps.get_db] = override_get_db
    original_sqlite_compat = app_main.ensure_sqlite_dev_schema_compatibility
    app_main.ensure_sqlite_dev_schema_compatibility = lambda: None

    try:
        user = crud.create_email_user(db_session, "profile@example.com", "abc12345", nickname="ProfileUser")
        user = crud.update_last_login_at(db_session, user)
        _create_ticket(db_session, user.id, "ticket-1")
        _create_ticket(db_session, user.id, "ticket-2")
        _create_ticket(db_session, user.id, "ticket-3")
        token = security.create_access_token(data={"sub": str(user.id)})

        with TestClient(app) as client:
            response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        body = response.json()
        assert body["nickname"] == "ProfileUser"
        assert body["travel_count"] == 3
    finally:
        app_main.ensure_sqlite_dev_schema_compatibility = original_sqlite_compat
        app.dependency_overrides.clear()
        db_session.close()
        Base.metadata.drop_all(bind=engine)
