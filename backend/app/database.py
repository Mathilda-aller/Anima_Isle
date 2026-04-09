# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库 URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

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

