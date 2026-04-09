# app/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app import crud, models, database
from app.utils import security

# 定义 Token 来源：请求头的 Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    安全依赖项
    解析 Token -> 拿到 UserID -> 查数据库 -> 返回用户对象
    如果 Token 无效，直接抛 401 错误，Router 根本不会执行。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub") #我们在 Token 里存了 user_id
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 数据库查用户
    user = crud.get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
    return user