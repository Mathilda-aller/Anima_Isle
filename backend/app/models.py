# app/models.py
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, JSON, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# ================= 1. 用户表 (User) =================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # MySQL 索引列必须指定长度
    email = Column(String(255), unique=True, index=True, nullable=True) 
    hashed_password = Column(String(255), nullable=True)
    wechat_openid = Column(String(64), unique=True, index=True, nullable=True)
    
    nickname = Column(String(64), default="Islander")
    avatar_url = Column(String(512), nullable=True) # URL 可能较长
    ui_style_pref = Column(String(20), default="Warm") 
    travel_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.now)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)

    tickets = relationship("Ticket", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    chat_logs = relationship("AIChatLog", back_populates="user")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")


# ================= 2. 聊天会话 (ChatSession) =================
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(64), primary_key=True, index=True) 
    user_id = Column(Integer, ForeignKey("users.id"))
    
    current_step = Column(Integer, default=0) 
    
    turn_1_answer = Column(Text, nullable=True)
    turn_2_answer = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="chat_sessions")


# ================= 3. 核心资产 (Ticket) =================
class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
 
    ticket_uid = Column(String(64), unique=True, index=True) 
    user_id = Column(Integer, ForeignKey("users.id"))
    
    image_url = Column(String(1024)) # URL 给长一点
    selected_image_id = Column(String(128), nullable=True)
    poem_content = Column(Text)
    image_style = Column(String(50)) 
    user_diary_summary = Column(Text)
    
    island_category = Column(String(50)) 
    selected_tags = Column(JSON)     
    is_public = Column(Boolean, default=False, nullable=False)
    
    is_printed_intent = Column(Boolean, default=False, nullable=False)
    
    view_count = Column(Integer, default=0)
    hug_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    
    reroll_count = Column(Integer, default=0, nullable=False)
    
    user = relationship("User", back_populates="tickets")


# ================= 4. AI 日志 (AIChatLog) =================
class AIChatLog(Base):
    __tablename__ = "ai_chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(String(64), index=True) 
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user_full_input = Column(Text)
    ai_reply_content = Column(Text)
    
    ai_risk_flag = Column(Boolean, default=False, nullable=False)
    ai_sentiment_score = Column(Float, nullable=True)
    
    duration_ms = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="chat_logs")


# ================= 5. 埋点事件 (TrackingEvent) =================
class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    event_name = Column(String(64), index=True) 
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    requested_ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="password_reset_tokens")


class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    code_hash = Column(String(128), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    send_count = Column(Integer, nullable=False, default=1)
    requested_ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
