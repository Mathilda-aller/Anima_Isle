# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def _normalize_database_url(database_url: str) -> str:
    url = make_url(database_url)
    if not url.drivername.startswith("mysql"):
        return database_url
    charset = str(url.query.get("charset") or "").lower()
    if charset == "utf8mb4":
        return database_url
    return url.update_query_dict({"charset": "utf8mb4"}).render_as_string(hide_password=False)


# 获取数据库 URL
SQLALCHEMY_DATABASE_URL = _normalize_database_url((os.getenv("DATABASE_URL") or "").strip())

if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("Missing DATABASE_URL environment variable")

# 检查是否是 SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # MySQL 不需要这个参数，传了会报错
    connect_args = {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    # 生产环境建议加这行，防止连接超时断开
    pool_pre_ping=True 
)

# 4. 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. ORM 基类
Base = declarative_base()
