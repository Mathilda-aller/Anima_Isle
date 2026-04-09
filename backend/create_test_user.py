# scripts/create_test_user.py
import sys
import os
# 把项目根目录加入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import crud, schemas
from app.utils.security import get_password_hash

db = SessionLocal()
# 创建一个测试用户
try:
    # 模拟一个邮箱注册请求
    user_in = schemas.UserLoginRequest(
        login_type="email",
        credential="test@anima.com",
        password="password123"
    )
    # 手动创建，因为 crud.create_user 会处理 hash
    user = crud.create_user(db, user_in)
    print(f"✅ 测试用户创建成功！账号: test@anima.com / 密码: password123")
except Exception as e:
    print(f"⚠️ 用户可能已存在或报错: {e}")
finally:
    db.close()