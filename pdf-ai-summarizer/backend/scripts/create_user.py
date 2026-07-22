"""
Tao tai khoan moi bang tay - khong co man hinh dang ky cong khai vi app nay
chi danh cho 1 nhom nho quen biet, ban (admin) tu tao tai khoan cho tung nguoi.

Dung nhanh (1 dong, khong hoi lai gi ca) - dung duoc ca luc chay local lan
luc dan vao tab "Console" tren Railway:
    .venv/bin/python scripts/create_user.py bach matkhau123 --display-name "Bach"

Bo trong mat khau de nhap kieu an (khong hien ra man hinh, an toan hon neu
go truoc mat nguoi khac):
    .venv/bin/python scripts/create_user.py bach
"""

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.auth_database import init_auth_db  # noqa: E402
from app.services.auth_service import create_user  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description="Tao tai khoan dang nhap moi")
    parser.add_argument("username")
    parser.add_argument("password", nargs="?", help="Bo trong de duoc hoi nhap an (khuyen khich)")
    parser.add_argument("--display-name", default="", help="Ten hien thi, mac dinh dung luon username")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Mat khau: ")

    await init_auth_db()
    user = await create_user(username=args.username, password=password, display_name=args.display_name)
    print(f"Da tao tai khoan thanh cong: {user.username} (id={user.id})")


if __name__ == "__main__":
    asyncio.run(main())
