# app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app import models, schemas
from app.utils.security import get_password_hash, verify_password # 导入刚才写的安全工具
import uuid
from datetime import datetime
from typing import Optional, List

# ================= 1. 用户与认证 (User & Auth) =================

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_openid(db: Session, openid: str):
    return db.query(models.User).filter(models.User.wechat_openid == openid).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def _default_nickname() -> str:
    return f"Islander_{str(uuid.uuid4())[:8]}"


def create_email_user(db: Session, email: str, password: str, nickname: Optional[str] = None) -> models.User:
    db_user = models.User(
        nickname=nickname or _default_nickname(),
        ui_style_pref="Warm",
        email=email,
        hashed_password=get_password_hash(password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_wechat_user(db: Session, openid: str, nickname: Optional[str] = None) -> models.User:
    db_user = models.User(
        nickname=nickname or _default_nickname(),
        ui_style_pref="Warm",
        wechat_openid=openid,
        hashed_password=None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user(db: Session, user: schemas.UserLoginRequest):
    # 兼容旧调用路径
    if user.login_type == "email":
        if not user.password:
            raise ValueError("Email login requires a password")
        return create_email_user(db, email=user.credential, password=user.password)
    if user.login_type == "wechat":
        return create_wechat_user(db, openid=user.credential)
    raise ValueError("Unsupported login type")


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    用户认证
    用于登录接口。验证 邮箱是否存在 + 密码是否匹配。
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_last_login_at(db: Session, user: models.User) -> models.User:
    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)
    return user


def create_password_reset_token(
    db: Session,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    requested_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> models.PasswordResetToken:
    reset_token = models.PasswordResetToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        requested_ip=requested_ip,
        user_agent=user_agent,
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def get_valid_reset_token(db: Session, token_hash: str) -> Optional[models.PasswordResetToken]:
    reset_token = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.token_hash == token_hash)
        .first()
    )
    if not reset_token:
        return None
    if reset_token.used_at is not None:
        return None
    if reset_token.expires_at < datetime.now():
        return None
    return reset_token


def mark_reset_token_used(db: Session, reset_token: models.PasswordResetToken) -> models.PasswordResetToken:
    reset_token.used_at = datetime.now()
    db.commit()
    db.refresh(reset_token)
    return reset_token


def update_user_password(db: Session, user: models.User, new_password: str) -> models.User:
    user.hashed_password = get_password_hash(new_password)
    user.password_changed_at = datetime.now()
    db.commit()
    db.refresh(user)
    return user


def create_email_verification_code(
    db: Session,
    email: str,
    code_hash: str,
    expires_at: datetime,
    send_count: int,
    requested_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> models.EmailVerificationCode:
    verification = models.EmailVerificationCode(
        email=email,
        code_hash=code_hash,
        expires_at=expires_at,
        send_count=send_count,
        requested_ip=requested_ip,
        user_agent=user_agent,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def get_latest_email_verification_code(db: Session, email: str) -> Optional[models.EmailVerificationCode]:
    return (
        db.query(models.EmailVerificationCode)
        .filter(models.EmailVerificationCode.email == email)
        .order_by(desc(models.EmailVerificationCode.created_at), desc(models.EmailVerificationCode.id))
        .first()
    )


def count_email_verification_codes_since(db: Session, email: str, since: datetime) -> int:
    return (
        db.query(func.count(models.EmailVerificationCode.id))
        .filter(
            models.EmailVerificationCode.email == email,
            models.EmailVerificationCode.created_at >= since,
        )
        .scalar()
        or 0
    )


def mark_email_verification_code_used(
    db: Session, verification: models.EmailVerificationCode
) -> models.EmailVerificationCode:
    verification.used_at = datetime.now()
    db.commit()
    db.refresh(verification)
    return verification


def update_user_style(db: Session, user_id: int, style: str):
    user = get_user_by_id(db, user_id)
    if user:
        user.ui_style_pref = style
        db.commit()
        db.refresh(user)
    return user

# ================= 2. 聊天会话 (Chat Session) =================

def create_chat_session(db: Session, user_id: int):
    session_uid = str(uuid.uuid4())
    db_session = models.ChatSession(
        session_id=session_uid,
        user_id=user_id,
        current_step=0, 
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_chat_session(db: Session, session_id: str):
    return db.query(models.ChatSession).filter(models.ChatSession.session_id == session_id).first()

def save_chat_answer(db: Session, session_id: str, answer: str, turn_index: int):
    db_session = get_chat_session(db, session_id)
    if not db_session:
        return None

    db_session.updated_at = datetime.now()
    if turn_index == 1:
        db_session.turn_1_answer = answer
    elif turn_index == 2:
        db_session.turn_2_answer = answer

    db.commit()
    db.refresh(db_session)
    return db_session

def update_chat_step(db: Session, session_id: str, step: int, answer: str = None, turn_index: int = 0):
    db_session = get_chat_session(db, session_id)
    if not db_session:
        return None
    
    db_session.current_step = step
    db_session.updated_at = datetime.now()
    
    if answer and turn_index == 1:
        db_session.turn_1_answer = answer
    elif answer and turn_index == 2:
        db_session.turn_2_answer = answer
        
    db.commit()
    db.refresh(db_session)
    return db_session

# ================= 3. 船票/资产 (Ticket) =================

def create_ticket(db: Session, ticket_data: dict, user_id: int):
    db_ticket = models.Ticket(
        ticket_uid=str(uuid.uuid4()),
        user_id=user_id,
        image_url=ticket_data.get("image_url"),
        selected_image_id=ticket_data.get("selected_image_id"),
        poem_content=ticket_data.get("poem_content"),
        image_style=ticket_data.get("image_style"),
        user_diary_summary=ticket_data.get("user_diary_summary"),
        island_category=ticket_data.get("island_category"),
        is_public=False,
        is_printed_intent=False,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_user_tickets(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.Ticket)\
             .filter(models.Ticket.user_id == user_id)\
             .order_by(desc(models.Ticket.created_at))\
             .offset(skip).limit(limit).all()

def mark_ticket_print_intent(db: Session, ticket_uid: str):
    ticket = db.query(models.Ticket).filter(models.Ticket.ticket_uid == ticket_uid).first()
    if ticket:
        ticket.is_printed_intent = True
        db.commit()
    return ticket


def get_ticket_by_uid(db: Session, ticket_uid: str):
    """通过业务ID查询 Ticket"""
    return db.query(models.Ticket).filter(models.Ticket.ticket_uid == ticket_uid).first()

def update_ticket_selection(
    db: Session,
    ticket_uid: str,
    image_url: str,
    style: Optional[str] = None,
    reroll_count: int = 0,
    selected_image_id: Optional[str] = None,
):
    """
    【Chat Confirm】更新用户最终选定的图片和风格
    场景：用户在前端 Reroll 了两次，最后选了 Style C，我们需要把数据库里的 image_url 改成 C 的链接。
    """
    ticket = get_ticket_by_uid(db, ticket_uid)
    if ticket:
        ticket.image_url = image_url
        if style:
            ticket.image_style = style
        ticket.selected_image_id = selected_image_id
        ticket.reroll_count = reroll_count
        db.commit()
        db.refresh(ticket)
    return ticket

# ================= 4. 埋点日志 (Tracking) =================

def create_tracking_log(db: Session, event: schemas.EventLogSchema):
    db_log = models.TrackingEvent(
        user_id=event.user_id,
        event_name=event.event_name,
        properties=event.properties
    )
    db.add(db_log)
    db.commit()
    return db_log

# ================= 4. 广场/共感地图 (Square) =================

def publish_ticket_to_island(db: Session, ticket_uid: str, tags: List[str]):
    """将卡片设为公开，并打上 Tag"""
    ticket = get_ticket_by_uid(db, ticket_uid)
    if ticket:
        ticket.is_public = True
        ticket.selected_tags = tags # 存入 JSON
        db.commit()
        db.refresh(ticket)
    return ticket

def get_public_tickets_by_island(db: Session, island_key: str, limit: int = 50):
    """
    获取某座岛屿下的公开卡片 (地图上的星星)
    实际生产中可能需要随机采样 (Random Sample)，这里先按时间倒序
    """
    return db.query(models.Ticket)\
             .filter(models.Ticket.is_public == True)\
             .filter(models.Ticket.island_category == island_key)\
             .order_by(desc(models.Ticket.created_at))\
             .limit(limit).all()

def increment_interaction(db: Session, ticket_uid: str, type: str):
    """点赞或抱抱"""
    ticket = get_ticket_by_uid(db, ticket_uid)
    if ticket:
        if type == "hug":
            ticket.hug_count += 1
        elif type == "view":
            ticket.view_count += 1
        # like_count 如果表里有的话也可以加
        db.commit()
        db.refresh(ticket)
    return ticket

def get_island_population(db: Session, island_key: str):
    """统计某座岛有多少公开卡片"""
    return db.query(models.Ticket)\
             .filter(models.Ticket.is_public == True)\
             .filter(models.Ticket.island_category == island_key)\
             .count()
