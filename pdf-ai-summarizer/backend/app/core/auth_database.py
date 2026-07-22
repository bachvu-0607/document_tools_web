import aiosqlite

from app.core.config import settings


async def init_auth_db() -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        await conn.commit()


async def create_user_record(
    user_id: str,
    username: str,
    password_hash: str,
    display_name: str,
    created_at: str,
) -> None:
    async with aiosqlite.connect(settings.database_path) as conn:
        await conn.execute(
            """
            INSERT INTO users (id, username, password_hash, display_name, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (user_id, username, password_hash, display_name, created_at),
        )
        await conn.commit()


async def get_user_by_username(username: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM users WHERE username = ?;", (username,))
        return await cursor.fetchone()


async def get_user_by_id(user_id: str) -> aiosqlite.Row | None:
    async with aiosqlite.connect(settings.database_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        return await cursor.fetchone()
