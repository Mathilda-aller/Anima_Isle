from datetime import datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, models, schemas
from app.database import Base
from app.routers import auth
from app.utils import mailer, security, wechat


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


def make_request(ip: str = "127.0.0.1", user_agent: str = "pytest"):
    return SimpleNamespace(
        client=SimpleNamespace(host=ip),
        headers={"user-agent": user_agent},
    )


def assert_http_error(exc_info, status_code: int, detail: str) -> None:
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


@pytest.mark.anyio
async def test_register_and_login_email_flow(db_session, monkeypatch):
    register_payload = schemas.EmailRegisterRequest(
        email="user1@example.com",
        password="abc12345",
        nickname="User1",
        verification_code="123456",
    )
    sent = {"count": 0}

    async def fake_send_register_verification_email(to_email: str, code: str):
        sent["count"] += 1
        assert to_email == "user1@example.com"
        assert code == "123456"

    monkeypatch.setattr(security, "generate_email_verification_code", lambda: "123456")
    monkeypatch.setattr(mailer, "send_register_verification_email", fake_send_register_verification_email)

    send_resp = await auth.send_register_verification_code(
        schemas.EmailVerificationSendRequest(email="user1@example.com"),
        make_request(),
        db_session,
    )
    assert send_resp.message == "verification_code_sent"

    register_resp = auth.register(register_payload, db_session)
    assert register_resp.token_type == "bearer"
    assert sent["count"] == 1

    with pytest.raises(HTTPException) as dup:
        auth.register(register_payload, db_session)
    assert_http_error(dup, 409, "email_exists")

    login_ok = await auth.login(
        schemas.UserLoginRequest(
            login_type="email",
            credential="user1@example.com",
            password="abc12345",
        ),
        db_session,
    )
    assert login_ok.user_info.nickname == "User1"

    with pytest.raises(HTTPException) as login_fail:
        await auth.login(
            schemas.UserLoginRequest(
                login_type="email",
                credential="user1@example.com",
                password="wrong1234",
            ),
            db_session,
        )
    assert_http_error(login_fail, 401, "Incorrect email or password")


@pytest.mark.anyio
async def test_send_register_code_rejects_existing_email(db_session):
    crud.create_email_user(db_session, "existing@example.com", "abc12345")

    with pytest.raises(HTTPException) as exc_info:
        await auth.send_register_verification_code(
            schemas.EmailVerificationSendRequest(email="existing@example.com"),
            make_request(),
            db_session,
        )
    assert_http_error(exc_info, 409, "email_exists")


@pytest.mark.anyio
async def test_send_register_code_cooldown(db_session, monkeypatch):
    async def fake_send_register_verification_email(to_email: str, code: str):
        return None

    monkeypatch.setattr(security, "generate_email_verification_code", lambda: "123456")
    monkeypatch.setattr(mailer, "send_register_verification_email", fake_send_register_verification_email)

    first = await auth.send_register_verification_code(
        schemas.EmailVerificationSendRequest(email="cooldown@example.com"),
        make_request(),
        db_session,
    )
    assert first.message == "verification_code_sent"

    with pytest.raises(HTTPException) as second:
        await auth.send_register_verification_code(
            schemas.EmailVerificationSendRequest(email="cooldown@example.com"),
            make_request(),
            db_session,
        )
    assert_http_error(second, 429, "verification_code_send_cooldown")


@pytest.mark.anyio
async def test_register_requires_valid_verification_code(db_session, monkeypatch):
    async def fake_send_register_verification_email(to_email: str, code: str):
        return None

    monkeypatch.setattr(security, "generate_email_verification_code", lambda: "123456")
    monkeypatch.setattr(mailer, "send_register_verification_email", fake_send_register_verification_email)

    await auth.send_register_verification_code(
        schemas.EmailVerificationSendRequest(email="verify@example.com"),
        make_request(),
        db_session,
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.register(
            schemas.EmailRegisterRequest(
                email="verify@example.com",
                password="abc12345",
                nickname="Verify",
                verification_code="654321",
            ),
            db_session,
        )
    assert_http_error(exc_info, 400, "verification_code_invalid")


def test_register_rejects_expired_verification_code(db_session):
    crud.create_email_verification_code(
        db=db_session,
        email="expired@example.com",
        code_hash=security.hash_email_verification_code("123456"),
        expires_at=datetime.now() - timedelta(minutes=1),
        send_count=1,
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.register(
            schemas.EmailRegisterRequest(
                email="expired@example.com",
                password="abc12345",
                nickname="Expired",
                verification_code="123456",
            ),
            db_session,
        )
    assert_http_error(exc_info, 400, "verification_code_expired")


def test_register_rejects_used_verification_code(db_session):
    verification = crud.create_email_verification_code(
        db=db_session,
        email="used@example.com",
        code_hash=security.hash_email_verification_code("123456"),
        expires_at=datetime.now() + timedelta(minutes=10),
        send_count=1,
    )
    crud.mark_email_verification_code_used(db_session, verification)

    with pytest.raises(HTTPException) as exc_info:
        auth.register(
            schemas.EmailRegisterRequest(
                email="used@example.com",
                password="abc12345",
                nickname="Used",
                verification_code="123456",
            ),
            db_session,
        )
    assert_http_error(exc_info, 400, "verification_code_used")


def test_register_accepts_still_valid_older_verification_code(db_session):
    crud.create_email_verification_code(
        db=db_session,
        email="older@example.com",
        code_hash=security.hash_email_verification_code("123456"),
        expires_at=datetime.now() + timedelta(minutes=10),
        send_count=1,
    )
    crud.create_email_verification_code(
        db=db_session,
        email="older@example.com",
        code_hash=security.hash_email_verification_code("654321"),
        expires_at=datetime.now() + timedelta(minutes=10),
        send_count=2,
    )

    register_resp = auth.register(
        schemas.EmailRegisterRequest(
            email="older@example.com",
            password="abc12345",
            nickname="Older",
            verification_code="123456",
        ),
        db_session,
    )

    assert register_resp.user_info.nickname == "Older"


@pytest.mark.anyio
async def test_forgot_password_unified_response(db_session, monkeypatch):
    user = crud.create_email_user(db_session, "user2@example.com", "abc12345")
    assert user.id is not None

    sent = {"count": 0}

    async def fake_send_password_reset_email(to_email: str, reset_url: str):
        sent["count"] += 1

    monkeypatch.setattr(mailer, "send_password_reset_email", fake_send_password_reset_email)

    existing = await auth.forgot_password(
        schemas.ForgotPasswordRequest(email="user2@example.com"),
        make_request(),
        db_session,
    )
    missing = await auth.forgot_password(
        schemas.ForgotPasswordRequest(email="missing@example.com"),
        make_request(),
        db_session,
    )

    assert existing == missing
    assert existing["message"] == auth.FORGOT_PASSWORD_UNIFIED_MSG
    assert sent["count"] == 1


@pytest.mark.anyio
async def test_reset_password_token_lifecycle(db_session, monkeypatch):
    crud.create_email_user(db_session, "user3@example.com", "abc12345")
    captured = {"url": None}

    async def fake_send_password_reset_email(to_email: str, reset_url: str):
        captured["url"] = reset_url

    monkeypatch.setattr(mailer, "send_password_reset_email", fake_send_password_reset_email)
    forgot = await auth.forgot_password(
        schemas.ForgotPasswordRequest(email="user3@example.com"),
        make_request(),
        db_session,
    )
    assert forgot["message"] == auth.FORGOT_PASSWORD_UNIFIED_MSG
    assert captured["url"] is not None

    parsed = urlparse(captured["url"])
    token = parse_qs(parsed.query)["token"][0]

    reset_ok = auth.reset_password(
        schemas.ResetPasswordRequest(token=token, new_password="newpass123"),
        db_session,
    )
    assert reset_ok["message"] == "Password has been reset successfully."

    with pytest.raises(HTTPException) as reset_reuse:
        auth.reset_password(
            schemas.ResetPasswordRequest(token=token, new_password="newpass124"),
            db_session,
        )
    assert_http_error(reset_reuse, 400, "invalid_or_expired_token")

    login_new = await auth.login(
        schemas.UserLoginRequest(
            login_type="email",
            credential="user3@example.com",
            password="newpass123",
        ),
        db_session,
    )
    assert login_new.user_info.id is not None


def test_reset_password_invalid_and_expired_token(db_session):
    user = crud.create_email_user(db_session, "user4@example.com", "abc12345")
    expired_plain = security.generate_reset_token()
    crud.create_password_reset_token(
        db=db_session,
        user_id=user.id,
        token_hash=security.hash_reset_token(expired_plain),
        expires_at=datetime.now() - timedelta(minutes=1),
    )

    with pytest.raises(HTTPException) as expired_resp:
        auth.reset_password(
            schemas.ResetPasswordRequest(token=expired_plain, new_password="newpass123"),
            db_session,
        )
    assert_http_error(expired_resp, 400, "invalid_or_expired_token")

    with pytest.raises(HTTPException) as forged_resp:
        auth.reset_password(
            schemas.ResetPasswordRequest(
                token="totally-forged-token-1234567890",
                new_password="newpass123",
            ),
            db_session,
        )
    assert_http_error(forged_resp, 400, "invalid_or_expired_token")


@pytest.mark.anyio
async def test_wechat_login_regression(db_session, monkeypatch):
    async def fake_code_to_session(code: str):
        return {"openid": "wx_openid_1", "session_key": "dummy"}

    monkeypatch.setattr(wechat, "code_to_session", fake_code_to_session)

    first = await auth.login(
        schemas.UserLoginRequest(login_type="wechat", credential="code_1", password=None),
        db_session,
    )
    second = await auth.login(
        schemas.UserLoginRequest(login_type="wechat", credential="code_2", password=None),
        db_session,
    )

    assert first.user_info.id == second.user_info.id
    user_count = db_session.query(models.User).filter(models.User.wechat_openid == "wx_openid_1").count()
    assert user_count == 1
