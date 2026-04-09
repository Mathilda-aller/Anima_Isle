import os
import logging
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def _build_mail_config() -> ConnectionConfig:
    port = int(os.getenv("SMTP_PORT", "587"))
    use_ssl_tls = port == 465
    return ConnectionConfig(
        MAIL_USERNAME=os.getenv("SMTP_USER", ""),
        MAIL_PASSWORD=os.getenv("SMTP_PASS", ""),
        MAIL_FROM=os.getenv("SMTP_FROM", ""),
        MAIL_PORT=port,
        MAIL_SERVER=os.getenv("SMTP_HOST", ""),
        MAIL_STARTTLS=not use_ssl_tls,
        MAIL_SSL_TLS=use_ssl_tls,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


def is_mail_configured() -> bool:
    conf = _build_mail_config()
    return bool(conf.MAIL_SERVER and conf.MAIL_FROM)


async def send_password_reset_email(to_email: str, reset_url: str) -> None:
    conf = _build_mail_config()
    if not conf.MAIL_SERVER or not conf.MAIL_FROM:
        logger.warning("SMTP is not configured. Skip sending reset email.")
        return

    html = (
        "<p>您好，</p>"
        "<p>我们收到了您的密码重置请求。</p>"
        f"<p>请点击以下链接重置密码（30分钟内有效）：<a href='{reset_url}'>{reset_url}</a></p>"
        "<p>如果这不是您本人操作，请忽略本邮件。</p>"
    )
    message = MessageSchema(
        subject="Anima Isle 密码重置",
        recipients=[to_email],
        body=html,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_register_verification_email(to_email: str, code: str) -> None:
    conf = _build_mail_config()
    if not conf.MAIL_SERVER or not conf.MAIL_FROM:
        raise RuntimeError("smtp_not_configured")

    html = (
        "<p>您好，</p>"
        "<p>这是您的 Anima Isle 注册验证码。</p>"
        f"<p style='font-size:24px;font-weight:bold;letter-spacing:4px'>{code}</p>"
        "<p>验证码 10 分钟内有效，仅可使用一次。</p>"
        "<p>如果这不是您本人操作，请忽略本邮件。</p>"
    )
    message = MessageSchema(
        subject="Anima Isle 注册验证码",
        recipients=[to_email],
        body=html,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
