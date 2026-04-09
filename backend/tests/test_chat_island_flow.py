import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, deps, models
from app.database import Base
from app.main import app
import app.main as app_main
from app.utils import ai_engine, risk_engine, search_engine, security


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

    async def _poem(*args, **kwargs):
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

    step1 = client.post("/chat/reply", json={"session_id": session_id, "content": "今天下雨"}, headers=headers)
    assert step1.status_code == 200
    assert step1.json()["state"] == "processing"

    step2 = client.post("/chat/reply", json={"session_id": session_id, "content": "我有点累"}, headers=headers)
    assert step2.status_code == 200
    body = step2.json()
    assert body["state"] == "finished"
    assert body["reply_text"] == "我在听你说。"
    assert body["ticket_data"]["poem_content"] == "第一行\n第二行\n第三行"
    assert body["ticket_data"]["island_category"] == "RAIN"
    assert len(body["ticket_data"]["recommended_tags"]) == 5
    assert len(body["ticket_data"]["candidate_images"]) == 3


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


def test_chat_reply_logs_new_stage_breakdown(client, db_session, monkeypatch, caplog):
    async def _risk(*args, **kwargs):
        return _safe_result()

    async def _empathy(*args, **kwargs):
        return "我在听你说。"

    async def _route(*args, **kwargs):
        return {"Island": "RAIN", "Intensity": "LOW"}

    async def _embedding(*args, **kwargs):
        return [0.1] * 1024

    async def _poem(*args, **kwargs):
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
    caplog.set_level(logging.INFO)
    session_id = client.post("/chat/start", headers=headers).json()["session_id"]
    client.post("/chat/reply", json={"session_id": session_id, "content": "今天下雨"}, headers=headers)
    client.post("/chat/reply", json={"session_id": session_id, "content": "我有点累"}, headers=headers)

    assert '"event": "chat.reply.request.end"' in caplog.text
    assert '"step_name": "risk_check"' in caplog.text
    assert '"step_name": "empathy_text"' in caplog.text
    assert '"step_name": "emotion_route"' in caplog.text
    assert '"step_name": "three_line_poem"' in caplog.text


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
