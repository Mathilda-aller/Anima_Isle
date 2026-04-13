from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, deps, models
from app.database import Base
from app.main import app
import app.main as app_main
from app.utils import security


def _create_ticket(
    db_session,
    user_id: int,
    ticket_uid: str,
    island_category: str,
    selected_tags: list[str],
    is_public: bool = True,
):
    ticket = models.Ticket(
        ticket_uid=ticket_uid,
        user_id=user_id,
        image_url=f"https://img/{ticket_uid}.jpg",
        poem_content=f"poem-{ticket_uid}",
        user_diary_summary=f"diary-{ticket_uid}",
        island_category=island_category,
        selected_tags=selected_tags,
        is_public=is_public,
        is_printed_intent=False,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return ticket


def _register_and_get_token(db_session) -> str:
    user = crud.create_email_user(
        db_session,
        email="square_user@example.com",
        password="abc12345",
        nickname="SquareUser",
    )
    user = crud.update_last_login_at(db_session, user)
    return security.create_access_token(data={"sub": str(user.id)})


def _auth_headers(db_session):
    return {"Authorization": f"Bearer {_register_and_get_token(db_session)}"}


def _test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[deps.get_db] = override_get_db
    original_sqlite_compat = app_main.ensure_sqlite_dev_schema_compatibility
    app_main.ensure_sqlite_dev_schema_compatibility = lambda: None
    client = TestClient(app)
    return client, original_sqlite_compat


def setup_function():
    app.dependency_overrides.clear()


def teardown_function():
    app.dependency_overrides.clear()


def test_island_tags_returns_fixed_count_and_dedupes():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session = session_local()

    try:
        user = crud.create_email_user(db_session, "owner1@example.com", "abc12345")
        _create_ticket(db_session, user.id, "ticket-a", "MIST", ["#坚持", "#希望"])
        _create_ticket(db_session, user.id, "ticket-b", "MIST", ["#坚持", "#努力"])
        _create_ticket(db_session, user.id, "ticket-c", "MIST", ["#加油", "#成功"])

        client, original_sqlite_compat = _test_client(db_session)
        try:
            response = client.get(
                "/square/island-tags/MIST",
                params={"limit": 3},
                headers=_auth_headers(db_session),
            )
        finally:
            client.close()
            app_main.ensure_sqlite_dev_schema_compatibility = original_sqlite_compat

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 3
        assert len({item["tag"] for item in body}) == 3
        expected_tags = {"#加油", "#成功", "#坚持", "#希望", "#努力"}
        assert {item["tag"] for item in body}.issubset(expected_tags)
        for item in body:
            if item["tag"] in {"#加油", "#成功"}:
                assert item["ticket_uid"] == "ticket-c"
            elif item["tag"] == "#希望":
                assert item["ticket_uid"] == "ticket-a"
            elif item["tag"] == "#努力":
                assert item["ticket_uid"] == "ticket-b"
            else:
                assert item["ticket_uid"] in {"ticket-a", "ticket-b"}
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


def test_island_tags_force_include_preferred_tag_when_available():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session = session_local()

    try:
        user = crud.create_email_user(db_session, "owner2@example.com", "abc12345")
        _create_ticket(db_session, user.id, "ticket-1", "RAIN", ["#呼吸", "#暂停"])
        _create_ticket(db_session, user.id, "ticket-2", "RAIN", ["#慢一点", "#想放空"])
        _create_ticket(db_session, user.id, "ticket-3", "RAIN", ["#看海", "#想放空"])

        client, original_sqlite_compat = _test_client(db_session)
        try:
            response = client.get(
                "/square/island-tags/RAIN",
                params={
                    "limit": 2,
                    "preferred_tag": "#看海",
                    "preferred_ticket_uid": "ticket-3",
                },
                headers=_auth_headers(db_session),
            )
        finally:
            client.close()
            app_main.ensure_sqlite_dev_schema_compatibility = original_sqlite_compat

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["tag"] == "#看海"
        assert body[0]["ticket_uid"] == "ticket-3"
        assert body[0]["from_user_selection"] is True
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


def test_island_tags_ignore_missing_preferred_tag_and_skip_private_tickets():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session = session_local()

    try:
        user = crud.create_email_user(db_session, "owner3@example.com", "abc12345")
        _create_ticket(db_session, user.id, "ticket-public", "CLOUD", ["#晴一点", "#安静"])
        _create_ticket(db_session, user.id, "ticket-private", "CLOUD", ["#只给自己"], is_public=False)

        client, original_sqlite_compat = _test_client(db_session)
        try:
            response = client.get(
                "/square/island-tags/CLOUD",
                params={
                    "limit": 3,
                    "preferred_tag": "#不存在",
                    "preferred_ticket_uid": "ticket-private",
                },
                headers=_auth_headers(db_session),
            )
        finally:
            client.close()
            app_main.ensure_sqlite_dev_schema_compatibility = original_sqlite_compat

        assert response.status_code == 200
        body = response.json()
        assert body == [
            {"tag": "#晴一点", "ticket_uid": "ticket-public", "from_user_selection": False},
            {"tag": "#安静", "ticket_uid": "ticket-public", "from_user_selection": False},
        ]
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)
