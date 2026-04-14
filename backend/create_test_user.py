import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import crud
from app.database import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a local test user.")
    parser.add_argument("--email", default="test@anima.com")
    parser.add_argument("--password", default="password123")
    parser.add_argument("--nickname", default="TestUser")
    parser.add_argument("--internal-tester", action="store_true", help="Mark this account as unlimited internal tester.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = crud.get_user_by_email(db, args.email)
        if user is None:
            user = crud.create_email_user(
                db,
                email=args.email,
                password=args.password,
                nickname=args.nickname,
            )
            print(f"✅ 测试用户创建成功！账号: {args.email} / 密码: {args.password}")
        else:
            print(f"ℹ️ 用户已存在：{args.email}")

        if args.internal_tester and not user.is_internal_tester:
            user = crud.update_user_internal_tester(db, user, True)
            print("✅ 已标记为无限额测试号")
        elif args.internal_tester:
            print("ℹ️ 该账号已经是无限额测试号")
    except Exception as exc:
        print(f"⚠️ 创建或更新测试用户失败: {exc}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
