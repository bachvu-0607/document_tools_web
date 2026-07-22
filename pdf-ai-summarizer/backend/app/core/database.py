import aiosqlite

from app.core.config import settings


async def init_db() -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS summary_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                document_id TEXT NOT NULL,
                document_name TEXT NOT NULL,
                summary_text TEXT NOT NULL,
                at_time TEXT NOT NULL
            );
        """)
        # Bang co the da ton tai tu truoc khi co tinh nang dang nhap - them cot
        # user_id bang ALTER TABLE (khong xoa du lieu cu). Ban ghi cu se mang
        # gia tri NULL, khong khop voi user_id that nao khi truy van, coi nhu
        # khong co chu - an toan hon gan bua cho 1 nguoi.
        try:
            await conn.execute("ALTER TABLE summary_history ADD COLUMN user_id TEXT;")
        except aiosqlite.OperationalError:
            pass  # cot da ton tai roi, bo qua
        await conn.commit()


async def save_summary_record(
    document_id: str,
    user_id: str,
    document_name: str,
    summary_text: str,
    at_time: str,
) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute(
            """
            INSERT INTO summary_history (document_id, user_id, document_name, summary_text, at_time)
            VALUES (?, ?, ?, ?, ?);
            """,
            (document_id, user_id, document_name, summary_text, at_time),
        )
        await conn.commit()


async def get_latest_summary(document_id: str, user_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT document_name, summary_text
            FROM summary_history
            WHERE document_id = ? AND user_id = ?
            ORDER BY id DESC
            LIMIT 1;
            """,
            (document_id, user_id),
        )
        return await cursor.fetchone()
