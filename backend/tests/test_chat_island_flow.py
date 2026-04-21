import asyncio
import logging
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, deps, models, schemas
from app.database import Base
from app.main import app
import app.main as app_main
from app.utils import ai_engine, risk_engine, search_engine, security
from app.routers import chat as chat_router


class _RiskResult:
    def __init__(self, level: str, hit_type: str = "rule", reason_code: str = "none", should_block: bool = False):
        self.level = level
        self.hit_type = hit_type
        self.reason_code = reason_code
        self.should_block = should_block


def _safe_result() -> _RiskResult:
    return _RiskResult(level="SAFE", should_block=False)


def _danger_result() -> _RiskResult:
    return _RiskResult(level="DANGER", reason_code="self_harm_intent", should_block=True)


def _candidate(image_id: str, idx: int) -> dict:
    return {
        "image_id": image_id,
        "image_url": f"https://img/{image_id}.jpg",
        "poem_content": f"poem-{idx}",
        "image_description": f"image-description-{idx}",
        "emotion_intensity": "LOW",
        "semantic_text": f"semantic-{idx}",
        "distance": 0.9 - idx * 0.01,
        "is_fallback": idx == 2,
    }


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[deps.get_db] = override_get_db
    original_sqlite_compat = app_main.ensure_sqlite_dev_schema_compatibility
    app_main.ensure_sqlite_dev_schema_compatibility = lambda: None
    with TestClient(app) as c:
        yield c
    app_main.ensure_sqlite_dev_schema_compatibility = original_sqlite_compat
    app.dependency_overrides.clear()


def _register_and_get_token(db_session) -> str:
    user = crud.create_email_user(
        db_session,
        email="island_user@example.com",
        password="abc12345",
        nickname="IslandUser",
    )
    user = crud.update_last_login_at(db_session, user)
    return security.create_access_token(data={"sub": str(user.id)})


def test_chat_reply_returns_finished_with_dynamic_poem(client, db_session, monkeypatch):
    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _empathy(*args, **kwargs):
        return "我在听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(_user_input, image_description, **kwargs):
        return f"诗句-{image_description}"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "generate_empathy_text", _empathy)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]

    step1 = client.post("/chat/reply", json={"session_id": session_id, "content": "今天下雨"}, headers=headers)
    assert step1.status_code == 200
    assert step1.json()["state"] == "processing"

    step2 = client.post("/chat/reply", json={"session_id": session_id, "content": "我有点累"}, headers=headers)
    assert step2.status_code == 200
    body = step2.json()
    assert body["state"] == "finished"
    assert body["reply_text"] == "我在听你说。"
    assert body["ticket_data"]["poem_content"] == "诗句-image-description-0"
    assert body["ticket_data"]["island_category"] == "RAIN"
    assert len(body["ticket_data"]["recommended_tags"]) == 5
    assert len(body["ticket_data"]["candidate_images"]) == 3
    assert [item["poem_content"] for item in body["ticket_data"]["candidate_images"]] == [
        "诗句-image-description-0",
        "诗句-image-description-1",
        "诗句-image-description-2",
    ]


def test_chat_reply_risk_blocked_uses_risk_engine(client, db_session, monkeypatch):
    async def _risk(*args, **kwargs):
        return _danger_result()

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]

    client.post("/chat/reply", json={"session_id": session_id, "content": "第一轮"}, headers=headers)
    step2 = client.post("/chat/reply", json={"session_id": session_id, "content": "第二轮"}, headers=headers)

    assert step2.status_code == 200
    assert step2.json()["state"] == "risk_blocked"


def test_chat_start_rejects_when_daily_ticket_limit_reached(client, db_session):
    user = crud.create_email_user(
        db_session,
        email="limit_reached@example.com",
        password="abc12345",
        nickname="LimitReached",
    )
    crud.create_ticket(db_session, {"image_url": "https://img/1.jpg", "poem_content": "1", "island_category": "RAIN"}, user.id)
    crud.create_ticket(db_session, {"image_url": "https://img/2.jpg", "poem_content": "2", "island_category": "RAIN"}, user.id)

    token = security.create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/chat/start", headers=headers)

    assert response.status_code == 429
    assert response.json()["detail"] == "daily_ticket_limit_reached"


def test_chat_reply_rejects_final_generation_when_daily_ticket_limit_reached(client, db_session, monkeypatch):
    async def _risk(*args, **kwargs):
        raise AssertionError("risk check should not run when daily limit is reached")

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)

    user = crud.create_email_user(
        db_session,
        email="reply_limit@example.com",
        password="abc12345",
        nickname="ReplyLimit",
    )
    session = crud.create_chat_session(db_session, user_id=user.id)
    crud.update_chat_step(db_session, session.session_id, step=1, answer="第一轮", turn_index=1)
    crud.create_ticket(db_session, {"image_url": "https://img/1.jpg", "poem_content": "1", "island_category": "RAIN"}, user.id)
    crud.create_ticket(db_session, {"image_url": "https://img/2.jpg", "poem_content": "2", "island_category": "RAIN"}, user.id)

    token = security.create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/chat/reply", json={"session_id": session.session_id, "content": "第二轮"}, headers=headers)

    assert response.status_code == 429
    assert response.json()["detail"] == "daily_ticket_limit_reached"
    refreshed = crud.get_chat_session(db_session, session.session_id)
    assert refreshed.current_step == 1
    assert refreshed.turn_2_answer == "第二轮"


def test_chat_reply_stream_rejects_final_generation_when_daily_ticket_limit_reached(client, db_session, monkeypatch):
    async def _risk(*args, **kwargs):
        raise AssertionError("risk check should not run when daily limit is reached")

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)

    user = crud.create_email_user(
        db_session,
        email="stream_limit@example.com",
        password="abc12345",
        nickname="StreamLimit",
    )
    session = crud.create_chat_session(db_session, user_id=user.id)
    crud.update_chat_step(db_session, session.session_id, step=1, answer="第一轮", turn_index=1)
    crud.create_ticket(db_session, {"image_url": "https://img/1.jpg", "poem_content": "1", "island_category": "RAIN"}, user.id)
    crud.create_ticket(db_session, {"image_url": "https://img/2.jpg", "poem_content": "2", "island_category": "RAIN"}, user.id)

    token = security.create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/chat/reply/stream", json={"session_id": session.session_id, "content": "第二轮"}, headers=headers)

    assert response.status_code == 429
    assert response.json()["detail"] == "daily_ticket_limit_reached"


def test_internal_tester_can_bypass_daily_ticket_limit(client, db_session, monkeypatch):
    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _empathy(*args, **kwargs):
        return "我在听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(_user_input, image_description, **kwargs):
        return f"诗句-{image_description}"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "generate_empathy_text", _empathy)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    user = crud.create_email_user(
        db_session,
        email="internal_tester@example.com",
        password="abc12345",
        nickname="InternalTester",
    )
    user = crud.update_user_internal_tester(db_session, user, True)
    crud.create_ticket(db_session, {"image_url": "https://img/1.jpg", "poem_content": "1", "island_category": "RAIN"}, user.id)
    crud.create_ticket(db_session, {"image_url": "https://img/2.jpg", "poem_content": "2", "island_category": "RAIN"}, user.id)

    token = security.create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    start_response = client.post("/chat/start", headers=headers)
    assert start_response.status_code == 200
    session_id = start_response.json()["session_id"]

    step1 = client.post("/chat/reply", json={"session_id": session_id, "content": "今天下雨"}, headers=headers)
    assert step1.status_code == 200

    step2 = client.post("/chat/reply", json={"session_id": session_id, "content": "我有点累"}, headers=headers)
    assert step2.status_code == 200
    assert step2.json()["state"] == "finished"


def test_chat_reply_logs_new_stage_breakdown(client, db_session, monkeypatch, caplog):
    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _empathy(*args, **kwargs):
        return "我在听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(_user_input, image_description, **kwargs):
        return f"诗句-{image_description}"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "generate_empathy_text", _empathy)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    caplog.set_level(logging.INFO)
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]
    client.post("/chat/reply", json={"session_id": session_id, "content": "今天下雨"}, headers=headers)
    client.post("/chat/reply", json={"session_id": session_id, "content": "我有点累"}, headers=headers)

    assert '"event": "chat.reply.request.end"' in caplog.text
    assert '"step_name": "risk_check"' in caplog.text
    assert '"step_name": "empathy_text"' in caplog.text
    assert '"step_name": "emotion_route"' in caplog.text
    assert '"step_name": "three_line_poem"' in caplog.text


def test_chat_reply_returns_friendly_error_for_unsupported_characters(client, db_session, monkeypatch):
    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]

    def raise_incorrect_string_value(*args, **kwargs):
        raise SQLAlchemyError("Incorrect string value: '\\xF0\\x9F\\x98\\x80'")

    monkeypatch.setattr(crud, "update_chat_step", raise_incorrect_string_value)

    response = client.post("/chat/reply", json={"session_id": session_id, "content": "今天😀"}, headers=headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "chat_contains_unsupported_characters"


def test_chat_reply_stream_emits_ack_risk_empathy_and_asset(client, db_session, monkeypatch):
    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _stream(*args, **kwargs):
        for item in ["我在", "听你说。"]:
            yield item

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(_user_input, image_description, **kwargs):
        return f"诗句-{image_description}"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "stream_empathy_text", _stream)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]
    client.post("/chat/reply", json={"session_id": session_id, "content": "今天下雨"}, headers=headers)

    with client.stream(
        "POST",
        "/chat/reply/stream",
        json={"session_id": session_id, "content": "我有点累"},
        headers=headers,
    ) as response:
        body = "".join(line.decode("utf-8") if isinstance(line, bytes) else line for line in response.iter_lines())

    assert response.status_code == 200
    assert "event: ack" in body
    assert "event: risk" in body
    assert "event: empathy_delta" in body
    assert "event: empathy_done" in body
    assert "event: asset_ready" in body
    assert "event: done" in body
    assert "诗句-image-description-2" in body


def test_chat_reply_stream_can_finish_after_frontend_timeout_budget(client, db_session, monkeypatch):
    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _stream(*args, **kwargs):
        yield "我在"
        yield "听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(*args, **kwargs):
        return "第一行\n第二行\n第三行"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    perf_values = iter([0.0, 0.0, 0.2, 0.4, 1.0, 2.0, 5.0, 6.0, 17.2])

    def fake_perf_counter():
        try:
            return next(perf_values)
        except StopIteration:
            return 17.2

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "stream_empathy_text", _stream)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)
    monkeypatch.setattr("app.routers.chat.time.perf_counter", fake_perf_counter)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]
    client.post("/chat/reply", json={"session_id": session_id, "content": "今天下雨"}, headers=headers)

    with client.stream(
        "POST",
        "/chat/reply/stream",
        json={"session_id": session_id, "content": "我有点累"},
        headers=headers,
    ) as response:
        body = "".join(line.decode("utf-8") if isinstance(line, bytes) else line for line in response.iter_lines())

    assert response.status_code == 200
    assert 'event: done' in body
    assert '"elapsed_ms":' in body


def test_chat_reply_cancels_sibling_task_when_route_fails(client, db_session, monkeypatch):
    cancelled = {"value": False}

    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _empathy(*args, **kwargs):
        return "我在听你说。"

    async def _route(*args, **kwargs):
        raise RuntimeError("route failed")

    async def _embedding(*args, **kwargs):
        try:
            await asyncio.sleep(1)
            return [0.1] * 1024
        except asyncio.CancelledError:
            cancelled["value"] = True
            raise

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "generate_empathy_text", _empathy)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]

    client.post("/chat/reply", json={"session_id": session_id, "content": "第一轮"}, headers=headers)
    step2 = client.post("/chat/reply", json={"session_id": session_id, "content": "第二轮"}, headers=headers)

    assert step2.status_code == 500
    assert cancelled["value"] is True


def test_chat_reply_generation_failure_keeps_session_retryable(client, db_session, monkeypatch):
    attempts = {"count": 0}

    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _empathy(*args, **kwargs):
        return "我在听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("poem failed")
        return "第一行\n第二行\n第三行"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "generate_empathy_text", _empathy)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]

    client.post("/chat/reply", json={"session_id": session_id, "content": "第一轮"}, headers=headers)
    failed = client.post("/chat/reply", json={"session_id": session_id, "content": "第二轮"}, headers=headers)

    assert failed.status_code == 500
    assert crud.get_chat_session(db_session, session_id).current_step == 1

    retried = client.post("/chat/reply", json={"session_id": session_id, "content": "第二轮重试"}, headers=headers)

    assert retried.status_code == 200
    assert retried.json()["state"] == "finished"
    assert crud.get_chat_session(db_session, session_id).current_step == 3
    assert db_session.query(models.Ticket).count() == 1


def test_confirm_ticket_updates_poem_with_selected_image(client, db_session):
    user = crud.create_email_user(
        db_session,
        email="confirm_ticket_poem@example.com",
        password="abc12345",
        nickname="ConfirmPoem",
    )
    ticket = crud.create_ticket(
        db_session,
        {
            "image_url": "https://img/original.jpg",
            "poem_content": "首图诗句",
            "island_category": "RAIN",
            "selected_image_id": "img-1",
        },
        user.id,
    )
    token = security.create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/chat/confirm",
        json={
            "ticket_uid": ticket.ticket_uid,
            "final_image_url": "https://img/reroll.jpg",
            "final_poem_content": "重选后的诗句",
            "reroll_count": 1,
        },
        headers=headers,
    )

    assert response.status_code == 200
    updated = crud.get_ticket_by_uid(db_session, ticket.ticket_uid)
    assert updated.image_url == "https://img/reroll.jpg"
    assert updated.poem_content == "重选后的诗句"
    assert updated.reroll_count == 1


def test_daily_ticket_count_only_includes_today(db_session):
    user = crud.create_email_user(
        db_session,
        email="count_today@example.com",
        password="abc12345",
        nickname="CountToday",
    )
    old_ticket = crud.create_ticket(
        db_session,
        {"image_url": "https://img/old.jpg", "poem_content": "old", "island_category": "RAIN"},
        user.id,
    )
    old_ticket.created_at = datetime.now() - timedelta(days=1)
    db_session.commit()

    crud.create_ticket(
        db_session,
        {"image_url": "https://img/new.jpg", "poem_content": "new", "island_category": "RAIN"},
        user.id,
    )

    assert crud.count_user_tickets_created_since(
        db_session,
        user.id,
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
    ) == 1


def test_chat_reply_risk_blocked_advances_session_and_skips_generation(client, db_session, monkeypatch):
    calls = {"route": 0, "embedding": 0}

    async def _risk(*args, **kwargs):
        return _danger_result()

    async def _route(*args, **kwargs):
        calls["route"] += 1
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        calls["embedding"] += 1
        return [0.1] * 1024

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)

    token = _register_and_get_token(db_session)
    headers = {"Authorization": f"Bearer {token}"}
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]

    client.post("/chat/reply", json={"session_id": session_id, "content": "第一轮"}, headers=headers)
    blocked = client.post("/chat/reply", json={"session_id": session_id, "content": "第二轮"}, headers=headers)

    assert blocked.status_code == 200
    assert blocked.json()["state"] == "risk_blocked"
    assert crud.get_chat_session(db_session, session_id).current_step == 2
    assert calls == {"route": 0, "embedding": 0}


@pytest.mark.anyio
async def test_chat_reply_stream_disconnect_after_risk_keeps_session_retryable(db_session, monkeypatch):
    state = {"disconnect": False}

    async def _risk(*args, **kwargs):
        state["disconnect"] = True
        return _safe_result()

    async def _stream(*args, **kwargs):
        yield "我在听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(*args, **kwargs):
        return "第一行\n第二行\n第三行"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "stream_empathy_text", _stream)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    user = crud.create_email_user(db_session, email="disconnect_after_risk@example.com", password="abc12345")
    session = crud.create_chat_session(db_session, user_id=user.id)
    crud.update_chat_step(db_session, session.session_id, step=1, answer="第一轮", turn_index=1)
    current_user = crud.get_user_by_id(db_session, user.id)
    reply_req = schemas.ChatReplyRequest(session_id=session.session_id, content="第二轮")
    trace_id = "trace_disconnect_risk"
    breakdown = {}

    session, full_context = await chat_router._save_q2_and_build_context(
        db=db_session,
        session=session,
        reply_req=reply_req,
        trace_id=trace_id,
        user_id=user.id,
        breakdown=breakdown,
    )

    async def _is_disconnected():
        return state["disconnect"]

    chunks = []
    async for chunk in chat_router._stream_final_reply_events(
        db=db_session,
        session=session,
        current_user=current_user,
        full_context=full_context,
        trace_id=trace_id,
        breakdown=breakdown,
        request_started=0.0,
        is_disconnected=_is_disconnected,
    ):
        chunks.append(chunk)

    assert any("event: ack" in chunk for chunk in chunks)
    assert not any("event: asset_ready" in chunk for chunk in chunks)
    assert crud.get_chat_session(db_session, session.session_id).current_step == 1
    assert db_session.query(models.Ticket).count() == 0
    assert db_session.query(models.AIChatLog).count() == 0


@pytest.mark.anyio
async def test_chat_reply_stream_disconnect_during_empathy_cancels_asset_work(db_session, monkeypatch):
    cancelled = {"embedding": False}
    yielded = {"count": 0}
    started = asyncio.Event()

    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _stream(*args, **kwargs):
        await started.wait()
        yield "我在"
        yielded["count"] += 1
        yield "听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        try:
            started.set()
            await asyncio.sleep(1)
            return [0.1] * 1024
        except asyncio.CancelledError:
            cancelled["embedding"] = True
            raise

    async def _poem(*args, **kwargs):
        return "第一行\n第二行\n第三行"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "stream_empathy_text", _stream)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    user = crud.create_email_user(db_session, email="disconnect_during_empathy@example.com", password="abc12345")
    session = crud.create_chat_session(db_session, user_id=user.id)
    crud.update_chat_step(db_session, session.session_id, step=1, answer="第一轮", turn_index=1)
    current_user = crud.get_user_by_id(db_session, user.id)
    reply_req = schemas.ChatReplyRequest(session_id=session.session_id, content="第二轮")

    session, full_context = await chat_router._save_q2_and_build_context(
        db=db_session,
        session=session,
        reply_req=reply_req,
        trace_id="trace_disconnect_empathy",
        user_id=user.id,
        breakdown={},
    )

    async def _is_disconnected():
        return yielded["count"] > 0

    chunks = []
    async for chunk in chat_router._stream_final_reply_events(
        db=db_session,
        session=session,
        current_user=current_user,
        full_context=full_context,
        trace_id="trace_disconnect_empathy",
        breakdown={},
        request_started=0.0,
        is_disconnected=_is_disconnected,
    ):
        chunks.append(chunk)

    assert any("event: empathy_delta" in chunk for chunk in chunks)
    assert cancelled["embedding"] is True
    assert crud.get_chat_session(db_session, session.session_id).current_step == 1
    assert db_session.query(models.Ticket).count() == 0


@pytest.mark.anyio
async def test_chat_reply_stream_disconnect_before_ticket_create_skips_persist(db_session, monkeypatch):
    state = {"disconnect": False}

    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _stream(*args, **kwargs):
        yield "我在听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(*args, **kwargs):
        state["disconnect"] = True
        return "第一行\n第二行\n第三行"

    def _search(*args, **kwargs):
        return [_candidate("img-1", 0), _candidate("img-2", 1), _candidate("img-3", 2)]

    monkeypatch.setattr(risk_engine, "check_text_risk", _risk)
    monkeypatch.setattr(ai_engine, "stream_empathy_text", _stream)
    monkeypatch.setattr(ai_engine, "classify_emotion_route", _route)
    monkeypatch.setattr(ai_engine, "get_embedding", _embedding)
    monkeypatch.setattr(ai_engine, "generate_three_line_poem", _poem)
    monkeypatch.setattr(search_engine, "search_island_candidates", _search)

    user = crud.create_email_user(db_session, email="disconnect_before_ticket@example.com", password="abc12345")
    session = crud.create_chat_session(db_session, user_id=user.id)
    crud.update_chat_step(db_session, session.session_id, step=1, answer="第一轮", turn_index=1)
    current_user = crud.get_user_by_id(db_session, user.id)
    reply_req = schemas.ChatReplyRequest(session_id=session.session_id, content="第二轮")

    session, full_context = await chat_router._save_q2_and_build_context(
        db=db_session,
        session=session,
        reply_req=reply_req,
        trace_id="trace_disconnect_before_ticket",
        user_id=user.id,
        breakdown={},
    )

    async def _is_disconnected():
        return state["disconnect"]

    chunks = []
    async for chunk in chat_router._stream_final_reply_events(
        db=db_session,
        session=session,
        current_user=current_user,
        full_context=full_context,
        trace_id="trace_disconnect_before_ticket",
        breakdown={},
        request_started=0.0,
        is_disconnected=_is_disconnected,
    ):
        chunks.append(chunk)

    assert any("event: empathy_done" in chunk for chunk in chunks)
    assert not any("event: asset_ready" in chunk for chunk in chunks)
    assert crud.get_chat_session(db_session, session.session_id).current_step == 1
    assert db_session.query(models.Ticket).count() == 0
