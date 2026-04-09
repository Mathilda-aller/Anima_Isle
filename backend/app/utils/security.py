# app/utils/security.py
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
import os
import re
import secrets
import hashlib

# 从环境变量读取
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_A_COMPLEX_STRING_IN_PROD")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # Token 有效期 7 天
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    【生产级】生成 JWT Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # 将过期时间写入 Token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_password_strength(password: str) -> bool:
    if not password:
        return False
    if len(password) < 8 or len(password) > 64:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


def generate_reset_token() -> str:
    return secrets.token_urlsafe(48)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_email_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def hash_email_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
