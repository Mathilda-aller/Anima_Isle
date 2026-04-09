from datetime import timedelta, datetime
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app import crud, schemas, deps
from app.utils import security, wechat, mailer

router = APIRouter()
logger = logging.getLogger(__name__)

FORGOT_PASSWORD_UNIFIED_MSG = "If the account exists, a reset email has been sent."
RESET_PASSWORD_WEB_URL = os.getenv("RESET_PASSWORD_WEB_URL", "https://example.com/reset-password")
FORGOT_PASSWORD_COOLDOWN_SECONDS = 60
FORGOT_PASSWORD_RATE_LIMIT_CACHE = {}
EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES = 10
EMAIL_VERIFICATION_CODE_COOLDOWN_SECONDS = 60
EMAIL_VERIFICATION_DAILY_LIMIT = 10


def _build_auth_response(user) -> schemas.AuthTokenResponse:
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return schemas.AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_info=schemas.AuthUserInfo(
            id=user.id,
            nickname=user.nickname,
            ui_style=user.ui_style_pref,
        ),
    )


@router.post("/register", response_model=schemas.AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    register_req: schemas.EmailRegisterRequest,
    db: Session = Depends(deps.get_db),
):
    if not security.validate_password_strength(register_req.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be 8-64 chars and contain letters and numbers.",
        )

    exists = crud.get_user_by_email(db, register_req.email)
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_exists")

    verification = crud.get_latest_email_verification_code(db, register_req.email)
    if not verification:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="verification_code_required")
    if verification.used_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="verification_code_used")
    if verification.expires_at < datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="verification_code_expired")
    if verification.code_hash != security.hash_email_verification_code(register_req.verification_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="verification_code_invalid")

    user = crud.create_email_user(
        db,
        email=register_req.email,
        password=register_req.password,
        nickname=register_req.nickname,
    )
    crud.mark_email_verification_code_used(db, verification)
    user = crud.update_last_login_at(db, user)
    return _build_auth_response(user)


@router.post("/register/send-code", response_model=schemas.MessageResponse)
async def send_register_verification_code(
    body: schemas.EmailVerificationSendRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    email = str(body.email)
    if crud.get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_exists")

    latest = crud.get_latest_email_verification_code(db, email)
    if latest and (datetime.now() - latest.created_at).total_seconds() < EMAIL_VERIFICATION_CODE_COOLDOWN_SECONDS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="verification_code_send_cooldown")

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    send_count = crud.count_email_verification_codes_since(db, email, today_start)
    if send_count >= EMAIL_VERIFICATION_DAILY_LIMIT:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="verification_code_daily_limit")

    code = security.generate_email_verification_code()
    expires_at = datetime.now() + timedelta(minutes=EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES)
    client_ip = request.client.host if request.client else None

    try:
        await mailer.send_register_verification_email(to_email=email, code=code)
    except RuntimeError as error:
        logger.error("Register verification mail unavailable: %s", error)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="smtp_not_configured")
    except Exception:
        logger.exception("Failed to send register verification email to %s", email)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="verification_code_send_failed")

    crud.create_email_verification_code(
        db=db,
        email=email,
        code_hash=security.hash_email_verification_code(code),
        expires_at=expires_at,
        send_count=send_count + 1,
        requested_ip=client_ip,
        user_agent=request.headers.get("user-agent"),
    )
    return schemas.MessageResponse(message="verification_code_sent")


@router.post("/login", response_model=schemas.AuthTokenResponse)
async def login(
    login_req: schemas.UserLoginRequest,
    db: Session = Depends(deps.get_db),
):
    user = None
    if login_req.login_type == "email":
        if not login_req.password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password is required for email login.",
            )
        user = crud.authenticate_user(db, login_req.credential, login_req.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    elif login_req.login_type == "wechat":
        code = login_req.credential
        wechat_data = await wechat.code_to_session(code)
        openid = wechat_data["openid"]
        if not openid:
            raise HTTPException(status_code=400, detail="Failed to retrieve OpenID")
        user = crud.get_user_by_openid(db, openid)
        if not user:
            user = crud.create_wechat_user(db, openid=openid)
    else:
        raise HTTPException(status_code=400, detail="Unsupported login type")

    user = crud.update_last_login_at(db, user)
    return _build_auth_response(user)


@router.post("/forgot-password")
async def forgot_password(
    body: schemas.ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    logger.info("Forgot password requested for email=%s", body.email)
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = (body.email, client_ip)
    now_ts = datetime.now().timestamp()
    last_ts = FORGOT_PASSWORD_RATE_LIMIT_CACHE.get(rate_limit_key, 0)
    if now_ts - last_ts < FORGOT_PASSWORD_COOLDOWN_SECONDS:
        logger.info("Forgot password throttled for email=%s ip=%s", body.email, client_ip)
        return {"message": FORGOT_PASSWORD_UNIFIED_MSG}

    user = crud.get_user_by_email(db, body.email)
    if not user:
        return {"message": FORGOT_PASSWORD_UNIFIED_MSG}

    if not user.hashed_password:
        # 微信账号无本地密码，按统一响应处理，避免泄露账户类型
        return {"message": FORGOT_PASSWORD_UNIFIED_MSG}

    plain_token = security.generate_reset_token()
    token_hash = security.hash_reset_token(plain_token)
    expires_at = datetime.now() + timedelta(minutes=security.RESET_TOKEN_EXPIRE_MINUTES)
    crud.create_password_reset_token(
        db=db,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        requested_ip=client_ip if client_ip != "unknown" else None,
        user_agent=request.headers.get("user-agent"),
    )
    logger.info("Created password reset token record for user_id=%s", user.id)
    FORGOT_PASSWORD_RATE_LIMIT_CACHE[rate_limit_key] = now_ts

    reset_url = f"{RESET_PASSWORD_WEB_URL}?token={plain_token}"
    await mailer.send_password_reset_email(to_email=body.email, reset_url=reset_url)
    return {"message": FORGOT_PASSWORD_UNIFIED_MSG}


@router.post("/reset-password")
def reset_password(
    body: schemas.ResetPasswordRequest,
    db: Session = Depends(deps.get_db),
):
    if not security.validate_password_strength(body.new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="weak_password",
        )

    token_hash = security.hash_reset_token(body.token)
    reset_token = crud.get_valid_reset_token(db, token_hash)
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_or_expired_token",
        )

    user = crud.get_user_by_id(db, reset_token.user_id)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_or_expired_token",
        )

    crud.update_user_password(db, user, body.new_password)
    crud.mark_reset_token_used(db, reset_token)
    logger.info("Password reset success for user_id=%s", user.id)
    return {"message": "Password has been reset successfully."}
