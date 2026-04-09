# app/schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# ================= 基础响应模型 =================
class BaseResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None

# ================= User 相关 =================
# 1. 登录/注册请求
class UserLoginRequest(BaseModel):
    login_type: str  # "wechat" | "email"
    credential: str  # 如果是 email，则是邮箱地址；如果是 wechat，这里填前端 wx.login 获取的 code
    password: Optional[str] = None


class EmailRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None
    verification_code: str = Field(min_length=6, max_length=6)


class EmailVerificationSendRequest(BaseModel):
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16, max_length=512)
    new_password: str

# 2. 用户信息返回 (脱敏，不返回密码)
class UserDTO(BaseModel):
    id: int
    nickname: str
    avatar_url: Optional[str] = None
    ui_style_pref: str
    travel_count: int
    
    # 允许从 ORM 模型读取数据
    model_config = ConfigDict(from_attributes=True)

# 3. 更新风格偏好
class UserStyleUpdate(BaseModel):
    style_pref: str # 'Warm' | 'Dark'


class AuthUserInfo(BaseModel):
    id: int
    nickname: str
    ui_style: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: AuthUserInfo

# ================= Chat 相关 =================
# 1. 开始会话响应
class ChatStartResponse(BaseModel):
    session_id: str
    first_question: str

# 2. 用户回复请求
class ChatReplyRequest(BaseModel):
    session_id: str
    content: str
    is_voice: bool = False
    duration: float = 0.0


class ChatVoiceTranscribeResponse(BaseModel):
    session_id: str
    question_index: int
    text: str
    duration: float
    is_final: bool = True


class CandidateImageDTO(BaseModel):
    image_id: Optional[str] = None
    image_url: str
    poem_content: str
    image_description: Optional[str] = None
    emotion_intensity: Optional[str] = None
    semantic_text: Optional[str] = None
    distance: Optional[float] = None
    is_fallback: bool = False


class ChatTicketDataDTO(BaseModel):
    id: int
    ticket_uid: str
    image_url: str
    poem_content: str
    island_category: str
    is_public: bool
    created_at: datetime
    recommended_tags: List[str] = Field(min_length=5, max_length=5)
    candidate_images: List[CandidateImageDTO] = Field(min_length=3, max_length=3)

# 3. 聊天过程中的响应
class ChatStepResponse(BaseModel):
    session_id: str
    state: str # 'processing' | 'finished'
    reply_text: str # 精灵说的话 (Q2 或 最终共鸣)
    
    # 如果 finished，下面会有值
    ticket_data: Optional[ChatTicketDataDTO] = None 

# ================= Ticket 相关 =================
# 1. 船票详情
class TicketDTO(BaseModel):
    id: int
    ticket_uid: str
    image_url: str
    poem_content: str
    user_diary_summary: Optional[str] = None
    island_category: str
    selected_tags: List[str] = []
    selected_image_id: Optional[str] = None
    is_public: bool
    created_at: datetime
    
    @field_validator("selected_tags", mode="before")
    @classmethod
    def normalize_selected_tags(cls, value):
        if value is None:
            return []
        return value

    model_config = ConfigDict(from_attributes=True)


# ================= Chat Confirm 相关 =================
class TicketConfirmRequest(BaseModel):
    ticket_uid: str        # 必须传 Ticket 的业务ID，确保更新对那张票
    final_image_url: str   # 用户最终看到的图 (可能是重随后的 Style B)
    final_style: Optional[str] = None  # 兼容字段，已弃用
    
    # 记录重新生成次数，最多两次
    reroll_count: int = 0 

# ================= Ticket Smoke Test 相关 =================
class TicketPrintResponse(BaseModel):
    ticket_uid: str
    is_printed_intent: bool
    message: str


    # ================= Tracking 相关 =================
class EventLogSchema(BaseModel):
    event_name: str
    user_id: Optional[int] = None
    properties: Dict[str, Any] = {}


# ================= Square/Map 相关 =================

# 1. 岛屿元数据 (用于地图概览)
class IslandMeta(BaseModel):
    key: str        # e.g. "Anxiety"
    name: str       # e.g. "焦虑岛"
    population: int # 岛上有多少人(卡片)

# 2. 发布卡片请求
class CardPublishRequest(BaseModel):
    ticket_uid: str
    selected_tags: List[str] # 用户选的 tag，如 ["#期末"]

# 3. 地图上的星星 (卡片) DTO
class MapStarDTO(BaseModel):
    ticket_uid: str
    image_url: str  
    poem_content: str
    selected_tags: List[str]
    hug_count: int
    view_count: int
    created_at: datetime
    
    @field_validator("selected_tags", mode="before")
    @classmethod
    def normalize_selected_tags(cls, value):
        if value is None:
            return []
        return value

    # 增加这个配置允许从 ORM 读取
    model_config = ConfigDict(from_attributes=True)
